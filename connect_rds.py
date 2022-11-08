import sys,os,logging,pymysql
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage
)
LINE_CHANNEL_ACCESS_TOKEN   = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
LINE_CHANNEL_SECRET         = os.environ['LINE_CHANNEL_SECRET']
LINE_BOT_API = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

rds_host = os.environ['RDS_HOST']
username = os.environ['USERNAME']
password = os.environ['PASSWORD']
db_name = os.environ['DB_NAME']
port = os.environ['PORT']

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

try:
    conn = pymysql.connect(host=rds_host,port=port,user=username,passwd=password,db=db_name,connect_timeout=5)

except pymysql.MySQLError as e:
    logging.error('ERROR: Unexpected error: Could not connect to MySQL instance.')
    logging.error(e)
    sys.exit()

logger.info("SUCCESS: Connection to RDS MySQL instance succeeded")
def handler(event, context):
    with conn.cursor() as cur:
        cur.execute("select * from ShiftManagementApp_shift")
        conn.commit()
        logging.debug(cur.fetchall())
    conn.commit()