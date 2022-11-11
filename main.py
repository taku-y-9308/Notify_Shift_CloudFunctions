from email import message
import sys,os,logging,psycopg2,json
from datetime import datetime, date, timedelta,timezone
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage
)
from linebot.exceptions import LineBotApiError

LINE_CHANNEL_ACCESS_TOKEN   = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
LINE_CHANNEL_SECRET         = os.environ['LINE_CHANNEL_SECRET']
LINE_BOT_API = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
LINE_HANDLER = WebhookHandler(LINE_CHANNEL_SECRET)

unix_socket = os.environ['INSTANCE_UNIX_SOCKET']
username = os.environ['DB_USER']
password = os.environ['DB_PASS']
dbname = os.environ['DB_NAME']

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

try:
    conn = psycopg2.connect(dbname=dbname,user=username,password=password,host=unix_socket)

except psycopg2.OperationalError as e:
    logging.error('ERROR: Unexpected error: Could not connect to PostgreSQL instance.')
    logging.error(e)
    sys.exit()

logger.info("SUCCESS: Connection to heroku PostgreSQL succeeded")
def handler(event, context):
    logger.info(event)
    """
    body_str = event["body"]
    body_dict = json.loads(body_str)
    logger.info(type(body_dict))
    line_user_id = body_dict["events"][0]["source"]["userId"]
    logger.info(f"line_user_id:{line_user_id}")
    signature = event["headers"]["x-line-signature"]
    body = event["body"]
    """
    #現在時刻(日本時間)を取得
    today = datetime.now(timezone(timedelta(hours=9))).date() #YYYY-MM-dd型で取得
    tomorrow = today + timedelta(days=1)
    #testdate = date(2022,7,30)
    
    with conn.cursor() as cur:
        
        #シフトを収集
        cur.execute('select "ShiftManagementApp_user".id,date,begin,finish,"ShiftManagementApp_user".username,"ShiftManagementApp_shift".user_id,line_user_id \
            from "ShiftManagementApp_shift" \
            inner join "ShiftManagementApp_user" \
            on "ShiftManagementApp_shift".user_id = "ShiftManagementApp_user".id \
            inner join "ShiftManagementApp_line_user_id" \
            on "ShiftManagementApp_user".id = "ShiftManagementApp_line_user_id".user_id '\
            +f"where date ='{tomorrow}';")
        results_shifts = cur.fetchall()
        logger.info(results_shifts)
        tomorrow_shift_lists = []
        for result_shift in results_shifts:
            tomorrow_shift_lists.append({
                "id" : result_shift[0],
                "date" : result_shift[1],
                "start" : result_shift[2],
                "end" : result_shift[3],
                "username" : result_shift[4],
                "user_id" : result_shift[5],
                "line_user_id" : result_shift[6]
            })
        logger.info(tomorrow_shift_lists)
        #logger.info(type(tomorrow_shift_lists[0]['date'])) #<class 'datetime.date'>
        #logger.info(type(tomorrow_shift_lists[0]['start'])) #<class 'datetime.datetime'>
        
        #LINE登録しているユーザーを取得
        cur.execute('select * from line_bot;')
        result_notify_list = cur.fetchall()
        logger.info(result_notify_list)
        
        reply_message = ""
    conn.commit()

    @LINE_HANDLER.add(MessageEvent, message=TextMessage)
    def on_message(line_event):
        LINE_BOT_API.reply_message(line_event.reply_token, TextSendMessage(reply_message))
    
    for tomorrow_shift_list in tomorrow_shift_lists:
        #LINE登録があるユーザーのみpush通知を行う
        if tomorrow_shift_list['line_user_id']:
            #日本時間に変換
            start_JST = tomorrow_shift_list['start'] + timedelta(hours=9)
            end_JST = tomorrow_shift_list['end'] + timedelta(hours=9)
            
            #LINEの宛先
            to = tomorrow_shift_list['line_user_id']

            push_message = f"お疲れ様です。\n明日のシフトを通知します。\n{start_JST.strftime('%H:%M')}〜{end_JST.strftime('%H:%M')}\nよろしくお願いします。"
            try:
                LINE_BOT_API.push_message(to, TextSendMessage(text=push_message))
                logger.info(f"メッセージが送信されました。 to:{to} push_message:{push_message}")
            except LineBotApiError as e:
                logger.error(e)
    """
    LINE_HANDLER.handle(body, signature)
    """
    return 0