import requests
import json
import time
import os

# ===== КОНФИГ (ТОКЕН ВСТАВЛЕН) =====
BOT_TOKEN = '8691315497:AAE5JuMOGKrQNLEmr-YckUJvNRhwoDB6AU4'
CHAT_IDS = ['7950533047', '5878306177']
LOG_FILE = 'visits.log'
OFFSET_FILE = 'offset.txt'
# ====================================

def get_updates(offset=0):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?timeout=10&offset={offset + 1}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get('result', [])
    except:
        return []

def send_telegram(chat_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    if keyboard:
        data['reply_markup'] = json.dumps(keyboard)
    try:
        requests.post(url, data=data)
    except:
        pass

def send_menu(chat_id):
    text = "🤖 <b>Статистика TENDO</b>\n\nВыберите отчёт:"
    keyboard = {
        'inline_keyboard': [
            [
                {'text': '📊 За день', 'callback_data': 'daily'},
                {'text': '📈 За час', 'callback_data': 'hourly'}
            ],
            [
                {'text': '📅 За месяц', 'callback_data': 'monthly'},
                {'text': '📊 Вся статистика', 'callback_data': 'total'}
            ]
        ]
    }
    send_telegram(chat_id, text, keyboard)

def send_daily_stats(chat_id):
    if not os.path.exists(LOG_FILE):
        send_telegram(chat_id, "📊 За день: 0 посетителей")
        return
    
    with open(LOG_FILE, 'r') as f:
        lines = f.readlines()
    
    today = time.strftime('%Y-%m-%d')
    count = 0
    unique = set()
    
    for line in lines:
        try:
            data = json.loads(line.strip())
            if data.get('time', '').startswith(today):
                count += 1
                unique.add(data.get('userAgent', ''))
        except:
            pass
    
    text = f"📊 <b>СТАТИСТИКА ЗА ДЕНЬ</b>\n📅 {time.strftime('%d.%m.%Y')}\n━━━━━━━━━━━━━━━\n👥 Посетителей: {count}\n👤 Уникальных: {len(unique)}"
    send_telegram(chat_id, text)

def send_hourly_stats(chat_id):
    if not os.path.exists(LOG_FILE):
        send_telegram(chat_id, "📈 За час: 0 посетителей")
        return
    
    with open(LOG_FILE, 'r') as f:
        lines = f.readlines()
    
    one_hour_ago = time.time() - 3600
    count = 0
    
    for line in lines:
        try:
            data = json.loads(line.strip())
            t = time.strptime(data.get('time', ''), '%Y-%m-%d %H:%M:%S')
            if time.mktime(t) >= one_hour_ago:
                count += 1
        except:
            pass
    
    text = f"📈 <b>СТАТИСТИКА ЗА ЧАС</b>\n🕒 {time.strftime('%H:%M')}\n━━━━━━━━━━━━━━━\n👥 Посетителей: {count}"
    send_telegram(chat_id, text)

def send_monthly_stats(chat_id):
    if not os.path.exists(LOG_FILE):
        send_telegram(chat_id, "📅 За месяц: 0 посетителей")
        return
    
    with open(LOG_FILE, 'r') as f:
        lines = f.readlines()
    
    month_start = time.strftime('%Y-%m-01')
    count = 0
    unique = set()
    
    for line in lines:
        try:
            data = json.loads(line.strip())
            if data.get('time', '').startswith(month_start):
                count += 1
                unique.add(data.get('userAgent', ''))
        except:
            pass
    
    days = int(time.strftime('%d'))
    avg = round(count / days) if days > 0 else 0
    
    text = f"📅 <b>СТАТИСТИКА ЗА МЕСЯЦ</b>\n📆 {time.strftime('%B %Y')}\n━━━━━━━━━━━━━━━\n👥 Посетителей: {count}\n👤 Уникальных: {len(unique)}\n🔄 Среднее в день: {avg}"
    send_telegram(chat_id, text)

def send_total_stats(chat_id):
    if not os.path.exists(LOG_FILE):
        send_telegram(chat_id, "📊 Всего: 0 посетителей")
        return
    
    with open(LOG_FILE, 'r') as f:
        lines = f.readlines()
    
    total = len(lines)
    unique = set()
    first = None
    
    for line in lines:
        try:
            data = json.loads(line.strip())
            if not first:
                first = data.get('time', '')
            unique.add(data.get('userAgent', ''))
        except:
            pass
    
    first_str = time.strftime('%d.%m.%Y %H:%M', time.strptime(first, '%Y-%m-%d %H:%M:%S')) if first else '—'
    
    text = f"📊 <b>ВСЯ СТАТИСТИКА</b>\n━━━━━━━━━━━━━━━\n👥 Всего визитов: {total}\n👤 Уникальных: {len(unique)}\n🕐 Первое посещение: {first_str}"
    send_telegram(chat_id, text)

# ===== ОСНОВНОЙ ЦИКЛ =====
print("🤖 Бот запущен!")
print(f"🤖 Токен: {BOT_TOKEN[:10]}...")

while True:
    try:
        last_offset = 0
        if os.path.exists(OFFSET_FILE):
            with open(OFFSET_FILE, 'r') as f:
                last_offset = int(f.read().strip())
        
        updates = get_updates(last_offset)
        
        for update in updates:
            chat_id = update.get('message', {}).get('chat', {}).get('id')
            text = update.get('message', {}).get('text', '')
            update_id = update.get('update_id', 0)
            
            if chat_id is None:
                continue
            
            if str(chat_id) not in CHAT_IDS:
                send_telegram(chat_id, "⛔ У вас нет доступа к этому боту.")
                continue
            
            if text == '/start':
                send_menu(chat_id)
            elif text in ['📊 За день', '/day']:
                send_daily_stats(chat_id)
            elif text in ['📈 За час', '/hour']:
                send_hourly_stats(chat_id)
            elif text in ['📅 За месяц', '/month']:
                send_monthly_stats(chat_id)
            elif text in ['📊 Вся статистика', '/total']:
                send_total_stats(chat_id)
            elif text == '/stats':
                send_menu(chat_id)
            else:
                send_menu(chat_id)
            
            if update_id > last_offset:
                with open(OFFSET_FILE, 'w') as f:
                    f.write(str(update_id + 1))
        
        time.sleep(5)
        
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(10)