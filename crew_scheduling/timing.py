from datetime import datetime, timedelta
import pytz


dep_tz = pytz.timezone('US/Eastern')
atd_lt = datetime(year=2019, month=11, day=15,
                  hour=9, minute=15, tzinfo=dep_tz)
zulu = pytz.utc
print('DEP')
print('LT {}'.format(atd_lt))
atd_z = atd_lt.astimezone(zulu)
print('Z  {}'.format(atd_z))


ft = timedelta(days=0, hours=6.5)
ata_z = atd_z + ft
print('ARR')
print('Z  {}'.format(ata_z))
print('{}:{}'.format(ata_z.hour, ata_z.minute))
# day year month
from tzwhere import tzwhere

tz = tzwhere.tzwhere()
arrival_zone = tz.tzNameAt(30.850307, 75.961716)

ata_lt = ata_z.astimezone(pytz.timezone(arrival_zone))
print('LT {}'.format(ata_lt))
