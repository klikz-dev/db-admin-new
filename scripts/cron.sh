# m h  dom mon dow   command

# Refresh all brands feed and inventory daily at 10 pm
0 22 * * * . /home/ubuntu/admin/venv/bin/activate && /home/ubuntu/admin/scripts/feed.sh > /dev/null 2>> /home/ubuntu/log/cron_error.log

# Sync orders every 5 min
*/5 * * * * . /home/ubuntu/admin/venv/bin/activate && python3 /home/ubuntu/admin/manage.py sync-order > /dev/null 2>> /home/ubuntu/log/cron_error.log

# Sync content hourly
0 * * * * . /home/ubuntu/admin/venv/bin/activate && python3 /home/ubuntu/admin/manage.py sync-content > /dev/null 2>> /home/ubuntu/log/cron_error.log

# Sync prices hourly
10 * * * * . /home/ubuntu/admin/venv/bin/activate && python3 /home/ubuntu/admin/manage.py sync-price > /dev/null 2>> /home/ubuntu/log/cron_error.log

# Sync status hourly
20 * * * * . /home/ubuntu/admin/venv/bin/activate && python3 /home/ubuntu/admin/manage.py sync-status > /dev/null 2>> /home/ubuntu/log/cron_error.log

# Sync tags hourly
30 * * * * . /home/ubuntu/admin/venv/bin/activate && python3 /home/ubuntu/admin/manage.py sync-tag > /dev/null 2>> /home/ubuntu/log/cron_error.log

# refresh feeds daily at 6 am
0 5 * * * . /home/ubuntu/admin/venv/bin/activate && python3 /home/ubuntu/admin/manage.py roomvo > /dev/null 2>> /home/ubuntu/log/cron_error.log
0 6 * * * . /home/ubuntu/admin/venv/bin/activate && python3 /home/ubuntu/admin/manage.py feed > /dev/null 2>> /home/ubuntu/log/cron_error.log

# Send sample reminder at 12 pm daily
0 12 * * * . /home/ubuntu/admin/venv/bin/activate && python3 /home/ubuntu/admin/manage.py klaviyo sample-reminder > /dev/null 2>> /home/ubuntu/log/cron_error.log

# EDI - Brewster
5 10,16 * * * . /home/ubuntu/admin/venv/bin/activate && python3 /home/ubuntu/admin/manage.py edi-brewster submit > /dev/null 2>> /home/ubuntu/log/cron_error.log
5 9,15 * * * . /home/ubuntu/admin/venv/bin/activate && python3 /home/ubuntu/admin/manage.py edi-brewster ref > /dev/null 2>> /home/ubuntu/log/cron_error.log

# EDI - Kravet
10 10,16 * * * . /home/ubuntu/admin/venv/bin/activate && python3 /home/ubuntu/admin/manage.py edi-kravet submit > /dev/null 2>> /home/ubuntu/log/cron_error.log
10 9,15 * * * . /home/ubuntu/admin/venv/bin/activate && python3 /home/ubuntu/admin/manage.py edi-kravet ref > /dev/null 2>> /home/ubuntu/log/cron_error.log
10 11,17 * * * . /home/ubuntu/admin/venv/bin/activate && python3 /home/ubuntu/admin/manage.py edi-kravet tracking > /dev/null 2>> /home/ubuntu/log/cron_error.log

# EDI - Phillips Collection
15 10,16 * * * . /home/ubuntu/admin/venv/bin/activate && python3 /home/ubuntu/admin/manage.py edi-phillipscollection submit > /dev/null 2>> /home/ubuntu/log/cron_error.log

# EDI - Scalamandre
20 10,16 * * * . /home/ubuntu/admin/venv/bin/activate && python3 /home/ubuntu/admin/manage.py edi-scalamandre submit > /dev/null 2>> /home/ubuntu/log/cron_error.log

# EDI - Schumacher
25 10,16 * * * . /home/ubuntu/admin/venv/bin/activate && python3 /home/ubuntu/admin/manage.py edi-schumacher submit > /dev/null 2>> /home/ubuntu/log/cron_error.log
25 9,15 * * * . /home/ubuntu/admin/venv/bin/activate && python3 /home/ubuntu/admin/manage.py edi-schumacher ref > /dev/null 2>> /home/ubuntu/log/cron_error.log
25 11,17 * * * . /home/ubuntu/admin/venv/bin/activate && python3 /home/ubuntu/admin/manage.py edi-schumacher tracking > /dev/null 2>> /home/ubuntu/log/cron_error.log

# EDI - York
30 10,16 * * * . /home/ubuntu/admin/venv/bin/activate && python3 /home/ubuntu/admin/manage.py edi-york submit > /dev/null 2>> /home/ubuntu/log/cron_error.log
30 9,15 * * * . /home/ubuntu/admin/venv/bin/activate && python3 /home/ubuntu/admin/manage.py edi-york ref > /dev/null 2>> /home/ubuntu/log/cron_error.log
