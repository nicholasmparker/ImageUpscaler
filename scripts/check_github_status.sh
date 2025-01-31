#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the repository name from the git config
REPO_URL=$(git config --get remote.origin.url)
REPO_NAME=$(echo $REPO_URL | sed 's/.*github.com[:\/]\(.*\).git/\1/')

# Get the current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Get the latest commit hash
COMMIT_SHA=$(git rev-parse HEAD)

echo -e "${YELLOW}Checking GitHub Actions status for ${REPO_NAME} (${BRANCH})...${NC}"

# Function to check workflow status
check_workflow_status() {
    # Get the workflow runs for this commit
    WORKFLOW_RUNS=$(curl -s -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/${REPO_NAME}/actions/runs?head_sha=${COMMIT_SHA}")
    
    # Check if there are any workflow runs
    TOTAL_COUNT=$(echo $WORKFLOW_RUNS | jq '.total_count')
    
    if [ "$TOTAL_COUNT" -eq "0" ]; then
        echo -e "${YELLOW}No workflow runs found for this commit yet. Waiting...${NC}"
        return 1
    fi
    
    # Get status of each workflow
    echo $WORKFLOW_RUNS | jq -r '.workflow_runs[] | "\(.name): \(.status) (\(.conclusion))"' | while read -r line; do
        NAME=$(echo $line | cut -d: -f1)
        STATUS=$(echo $line | cut -d: -f2- | cut -d'(' -f1 | xargs)
        CONCLUSION=$(echo $line | cut -d'(' -f2 | cut -d')' -f1)
        
        case $STATUS in
            "completed")
                if [ "$CONCLUSION" == "success" ]; then
                    echo -e "${GREEN}✓ $NAME: Success${NC}"
                else
                    echo -e "${RED}✗ $NAME: $CONCLUSION${NC}"
                fi
                ;;
            "in_progress")
                echo -e "${YELLOW}⟳ $NAME: In Progress${NC}"
                ;;
            *)
                echo -e "${YELLOW}? $NAME: $STATUS${NC}"
                ;;
        esac
    done
    
    # Check if any workflows are still in progress
    IN_PROGRESS=$(echo $WORKFLOW_RUNS | jq '.workflow_runs[] | select(.status != "completed")')
    if [ ! -z "$IN_PROGRESS" ]; then
        return 1
    fi
    
    return 0
}

# Try up to 5 times, waiting 30 seconds between attempts
for i in {1..5}; do
    if check_workflow_status; then
        exit 0
    fi
    if [ $i -lt 5 ]; then
        echo -e "${YELLOW}Waiting 30 seconds before checking again...${NC}"
        sleep 30
    fi
done

echo -e "${YELLOW}Workflow check timeout. Please check GitHub Actions dashboard for status.${NC}"
echo -e "${YELLOW}https://github.com/${REPO_NAME}/actions${NC}"
