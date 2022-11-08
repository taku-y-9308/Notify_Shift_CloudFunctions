from email import message
import sys,os,logging,psycopg2,json
from datetime import datetime, date, timedelta,timezone
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, FollowEvent, TemplateSendMessage, ButtonsTemplate, PostbackAction, MessageAction, URIAction, AccountLinkEvent
)
from linebot.exceptions import LineBotApiError

LINE_CHANNEL_ACCESS_TOKEN   = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
LINE_CHANNEL_SECRET         = os.environ['LINE_CHANNEL_SECRET']
LINE_BOT_API = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
LINE_HANDLER = WebhookHandler(LINE_CHANNEL_SECRET)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def handler(event, context):
    body_str = event["body"]
    body_dict = json.loads(body_str)
    line_user_id = body_dict["events"][0]["source"]["userId"]
    signature = event["headers"]["x-line-signature"]
    body = event["body"]
    
    """textメッセージを受信"""
    @LINE_HANDLER.add(MessageEvent, message=TextMessage)
    def on_message(line_event):
        LINE_BOT_API.reply_message(line_event.reply_token, TextSendMessage("test message"))
    
    """"Followイベントを受信"""
    @LINE_HANDLER.add(FollowEvent)
    def send_account_linkage_url(event):
        user_id = event.source.user_id
        logger.info(f'Followイベントを受信しました。 line_user_id:{user_id}')
        link_token_response = LINE_BOT_API.issue_link_token(user_id)
        buttons_template_message = TemplateSendMessage(
            alt_text='Account Link',
            template=ButtonsTemplate(
                title='LINEアカウント連携',
                text='下のボタンよりLINEアカウントの連携を行ってください',
                actions=[
                    URIAction(
                        label='LINEアカウント連携',
                        uri="https://shiftmanagementapp-heroku.herokuapp.com/account_linkage?linkToken="+str(link_token_response.link_token)
                    )
                ]
            )
        )
        LINE_BOT_API.push_message(user_id, buttons_template_message)

    """AccountLinkEventを受信"""
    @LINE_HANDLER.add(AccountLinkEvent)
    def account_linkage(event):
        line_user_id = event.source.user_id
        nonce = event.link.nonce
        logger.info(f"AccountLinkEventを受信しました。user_id:{line_user_id},nonce:{nonce}")
        
        #heroku postgerSQLに接続
        host = os.environ['HOST']
        username = os.environ['USERNAME']
        password = os.environ['PASSWORD']
        dbname = os.environ['DB_NAME']
        port = os.environ['PORT']
        
        try:
            conn = psycopg2.connect(f"dbname={dbname} user={username} password={password} host={host} port={port}")
        
        except psycopg2.OperationalError as e:
            logging.error('ERROR: Unexpected error: Could not connect to PostgreSQL instance.')
            logging.error(e)
            sys.exit()
        
        logger.info("SUCCESS: Connection to heroku PostgreSQL succeeded")

        try:
            with conn.cursor() as cur:
                cur.execute(f"""UPDATE "ShiftManagementApp_line_user_id" SET line_user_id = '{line_user_id}' WHERE nonce = '{nonce}';""")
            conn.commit()
            logger.info("SUCCESS: DBの更新が正常に終了しました")
        except Exception as e:
            logger.error('ERROR: DB更新時にエラーが発生しました')
            logger.error(e)
            sys.exit()
        
        success_message = '連携完了しました'
        LINE_BOT_API.push_message(line_user_id, TextSendMessage(text=success_message))
        logger.info('連携完了メッセージの送信が完了しました')
    LINE_HANDLER.handle(body, signature)
    return 0
    