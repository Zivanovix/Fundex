#!/usr/bin/env bash
# Runs the IEP grader against the deployed system.
#
#   ./test.sh                  full run (authentication + blockchain)
#   ./test.sh --reset          clear the databases first, then run
#   ./test.sh --no-blockchain  run in BLOCKCHAIN_ENABLED=false mode
#
# --reset wipes data in place rather than redeploying: recreating every Service
# forces CoreDNS to reload, and while it does, service names can briefly fail to
# resolve inside the pods.
set -euo pipefail

cd "$(dirname "$0")"

HOST=127.0.0.1
AUTH_PORT=30000
EMPLOYEE_PORT=30001
DIRECTOR_PORT=30002
GANACHE_PORT=30003
JWT_SECRET=super-secret-key-change-in-production
SEEDED_DIRECTOR=onlymoney@gmail.com
POD_COUNT=9

RESET=false
BLOCKCHAIN=true

for argument in "$@"; do
    case "$argument" in
        --reset)          RESET=true ;;
        --no-blockchain)  BLOCKCHAIN=false ;;
        *) echo "Unknown option: $argument"; echo "Usage: $0 [--reset] [--no-blockchain]"; exit 1 ;;
    esac
done

if [ ! -x grader-venv/bin/python ]; then
    echo "grader-venv is missing. Create it once with:"
    echo "  python3 -m venv grader-venv"
    echo "  grader-venv/bin/pip install -r iep_grader/requirements-pytest.txt \"setuptools<81\""
    exit 1
fi

wait_for_pods() {
    local deadline=$((SECONDS + 300))
    until [ "$(kubectl get pods --no-headers 2>/dev/null | grep -c '1/1.*Running')" -ge "$POD_COUNT" ]; do
        if [ $SECONDS -gt $deadline ]; then
            echo "Timed out waiting for $POD_COUNT pods. Current state:"
            kubectl get pods
            exit 1
        fi
        sleep 5
    done
}

config_value() {
    kubectl get configmap fundex-config -o jsonpath="{.data.$1}"
}

echo "==> Waiting for $POD_COUNT pods to be ready"
wait_for_pods

if [ "$(config_value BLOCKCHAIN_ENABLED)" != "$BLOCKCHAIN" ]; then
    echo "==> Switching BLOCKCHAIN_ENABLED to $BLOCKCHAIN"
    kubectl patch configmap fundex-config \
        -p "{\"data\":{\"BLOCKCHAIN_ENABLED\":\"$BLOCKCHAIN\"}}" >/dev/null
    kubectl rollout restart deployment/director >/dev/null
    kubectl rollout status deployment/director --timeout=180s >/dev/null
    wait_for_pods
fi

if [ "$RESET" = true ]; then
    echo "==> Clearing databases"

    mongo_database=$(config_value MONGO_URI | sed 's#.*/##')
    kubectl exec deployment/mongo -- \
        mongosh "$mongo_database" --quiet --eval 'db.assets.deleteMany({})' >/dev/null

    kubectl exec deployment/redis -- redis-cli FLUSHALL >/dev/null

    db_user=$(config_value DB_USER)
    db_name=$(config_value DB_NAME)
    db_password=$(kubectl get secret fundex-secret -o jsonpath='{.data.DB_PASSWORD}' | base64 -d)
    kubectl exec deployment/mysql -- \
        mysql -u"$db_user" -p"$db_password" "$db_name" \
        -e "DELETE FROM users WHERE email <> '$SEEDED_DIRECTOR';" 2>/dev/null
fi

ARGS=(
    -q --type all
    --wait-for-services
    --authentication-url "http://$HOST:$AUTH_PORT"
    --jwt-secret "$JWT_SECRET"
    --roles-field role --employee-role employee --director-role director
    --with-authentication
    --employee-url "http://$HOST:$EMPLOYEE_PORT"
    --director-url "http://$HOST:$DIRECTOR_PORT"
    --grade-report-file grade_report.json
)

if [ "$BLOCKCHAIN" = true ]; then
    ARGS+=(--with-blockchain --provider-url "http://$HOST:$GANACHE_PORT")
fi

echo "==> Running grader (blockchain: $BLOCKCHAIN)"
echo
cd iep_grader
exec ../grader-venv/bin/python -m pytest "${ARGS[@]}"
