#coding:UTF-8

from threading import Timer
import logging
import urllib2
import re
import smtplib
from email.MIMEText import MIMEText
from email.Utils import formatdate


#------------------------------------------------------------------------------
# ユーザ設定値
#------------------------------------------------------------------------------

# 実行間隔(秒)
INTERVAL_SECOND = 10

# IPアドレス更新を告げるサイト
DDNS_UPDATE_URL = 'http://ddo.jp/dnsupdate.php?dn=ドメイン&pw=パスワード'

# 自分のWAN側IPアドレスを返してくれるサイト。複数指定可能
IP_CHECK_URL_LIST = ['http://checkip.dyndns.org', 'http://info.ddo.jp/remote_addr.php']

#エラー発生時のメール通知
SMTP_HOST = 'hoge.com'
SMTP_PORT = 587
MAIL_FROM = 'system@hoge.com'
MAIL_TO_LIST = ['hoge@hoge.com', 'hoge2@hoge.com']


#------------------------------------------------------------------------------
# 定数
#------------------------------------------------------------------------------

# IPアドレス記録ファイル名
IP_ADDRESS_FILE = 'ipaddress'

# IPアドレスを示す正規表現
IP_ADDRESS_PATTARN = re.compile('\d+\.\d+\.\d+\.\d+')

#------------------------------------------------------------------------------
# ログ設定
#------------------------------------------------------------------------------
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='updateddns.log',
                    filemode='a')

#------------------------------------------------------------------------------
# 関数
#------------------------------------------------------------------------------


def sendMail(body):
    """ メール送信 """
    msg = MIMEText(body)
    msg['Subject'] = 'DDNS更新エラー通知'
    msg['From'] = MAIL_FROM
    msg['To'] = MAIL_TO_LIST
    msg['Date'] = formatdate()
    s = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    s.sendmail(fromAddr, [toAddr], msg.as_string())
    s.close()


def getCurrentIpAddress(urlList):
    """ 指定されたURLリストから現在割り当てられているIPアドレスを取得する """
    for url in urlList:
        for line in urllib2.urlopen(url):
            matchResult = IP_ADDRESS_PATTARN.search(line)
            if matchResult != None:
                return matchResult.group()
    return None


def getLastIpAddress(fileName):
    """ 指定されたファイルに書かれたIPアドレスを取得する """
    lastIpAddress = ''
    try:
        f = open(IP_ADDRESS_FILE, 'r')
        for line in f:
            matchResult = IP_ADDRESS_PATTARN.search(line)
            if matchResult != None:
                lastIpAddress = matchResult.group()
        f.close()
    except IOError:
        pass
    return lastIpAddress


def updateIpAddress(ipAddress, updateUrl, fileName):
    """ 指定されたIPアドレスをもって指定されたDDNSとファイルの更新を行う """

    for line in urllib2.urlopen(updateUrl):
        if line.find('FAIL'):
            logging.error('fail to update. url=' + updateUrl)
            return False

    try:
        f = open(fileName, 'w')
        f.write(ipAddress)
        f.close()
    except IOError:
        logging.error('fail to write. file=' + fileName)
        return False

    logging.info('update with ' + currentIpAddress)
    return True


def mainThread():
    """ 実メイン処理 """
    logging.debug('start')

    # 現在のIPアドレスを取得
    currentIpAddress = getCurrentIpAddress(IP_CHECK_URL_LIST)

    # 前回のIPアドレスを取得
    lastIpAddress = getLastIpAddress(IP_ADDRESS_FILE)

    # 両者を比較し異なれば更新処理
    if lastIpAddress != currentIpAddress:
        success = updateIpAddress(currentIpAddress, DDNS_UPDATE_URL, IP_ADDRESS_FILE)
        if not success:
            # 更新エラーなのでメール送信してアプリ終了
            sendMail('DDNS更新に失敗したのでアプリを停止します。')
            return

    # 再帰呼び出し
    startTimer(INTERVAL_SECOND)


def startTimer(interval):
    """ 再帰的に呼び出されるスレッド実行関数 """
    t = Timer(interval, mainThread)
    t.start()

#------------------------------------------------------------------------------
# ここからプログラムスタートです。
#------------------------------------------------------------------------------
if __name__ == '__main__':
    startTimer(0)
