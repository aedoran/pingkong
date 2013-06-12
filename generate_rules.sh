#!/bin/sh

# This script will check if the rules have changed, and then attempt to generate html
# and add them to the current commit

cd "$(git rev-parse --show-toplevel)"

if git diff --exit-code --cached -- static/rules.md > /dev/null; then
    # no changes, exit
    exit 0
fi

echo "Time to party: generating new rules"

RULES_TEMPLATE='templates/rules.html'

markdown static/rules.md | cat $RULES_TEMPLATE.head - $RULES_TEMPLATE.tail > $RULES_TEMPLATE
git add $RULES_TEMPLATE
