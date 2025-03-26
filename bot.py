import sys
sys.path.insert(0, '.')
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from instagram_manager import InstagramBot
import threading
import config
from datetime import datetime

bot = InstagramBot()
stop_event = threading.Event()
interaction_stats = {'total': 0, 'last_targets': []}  # لتخزين الإحصائيات

# لوحة المفاتيح الرئيسية
KEYBOARD_MAIN = ReplyKeyboardMarkup([
    ['▶️ تشغيل البوت'],
    ['📊 الإحصائيات']
], resize_keyboard=True)

# لوحة المفاتيح أثناء التشغيل
KEYBOARD_RUNNING = ReplyKeyboardMarkup([
    ['⏸ إيقاف مؤقت', '🔄 تعديل الاستهدافات'],
    ['📊 الإحصائيات']
], resize_keyboard=True)

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    context.user_data.clear()
    update.message.reply_text(
        f"مرحبًا {user.first_name}! 👋\n"
        "أنا بوت تفاعل إنستجرام الذكي\n"
        "اضغط ▶️ تشغيل البوت لبدء الإعدادات",
        reply_markup=KEYBOARD_MAIN
    )

def show_stats(update: Update):
    stats = (f"📊 إحصائيات التفاعل:\n"
             f"• عدد الحسابات المستهدفة: {len(interaction_stats['last_targets']}\n"
             f"• إجمالي التفاعلات: {interaction_stats['total']}\n"
             f"• آخر تشغيل: {interaction_stats.get('last_run', 'لم يبدأ بعد')}")
    update.message.reply_text(stats)

def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    
    if text == "📊 الإحصائيات":
        show_stats(update)
        return
        
    if text == "▶️ تشغيل البوت":
        context.user_data.clear()
        update.message.reply_text("🔑 أرسل اسم مستخدم إنستجرام:", reply_markup=KEYBOARD_MAIN)
        context.user_data['step'] = "waiting_username"
    
    elif text == "🔄 تعديل الاستهدافات":
        update.message.reply_text(
            "أرسل الحسابات المستهدفة الجديدة (مفصولة بمساحة):",
            reply_markup=KEYBOARD_MAIN
        )
        context.user_data['step'] = "waiting_targets"
        stop_event.set()
        return
    
    elif text == "⏸ إيقاف مؤقت":
        stop_event.set()
        update.message.reply_text(
            "⏸ تم إيقاف البوت مؤقتًا\n"
            "اضغط ▶️ تشغيل البوت للمتابعة",
            reply_markup=KEYBOARD_MAIN
        )
        return
    
    # باقي معالجة الخطوات (تسجيل الدخول، إدخال الاستهدافات...)
    # ... [الكود السابق يبقى كما هو مع تعديل لوحات المفاتيح]
    
    elif context.user_data.get('step') == "waiting_targets":
        targets = [t.strip() for t in text.split() if t.strip()]
        if not targets:
            update.message.reply_text("⚠️ لم يتم إدخال حسابات مستهدفة")
            return
        
        interaction_stats['last_targets'] = targets
        interaction_stats['last_run'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        update.message.reply_text(
            f"⚡ بدء التفاعل مع {len(targets)} حساب...\n"
            "يمكنك إيقاف البوت أو تعديل الاستهدافات بأي وقت",
            reply_markup=KEYBOARD_RUNNING
        )
        
        stop_event.clear()
        thread = threading.Thread(
            target=run_interactions,
            args=(update, targets, stop_event)
        thread.start()

def run_interactions(update: Update, targets, stop_event):
    try:
        for target in targets:
            if stop_event.is_set():
                break
                
            followers = bot.get_followers(target)
            for i, user_id in enumerate(followers, 1):
                if stop_event.is_set():
                    return
                
                if bot.interact_with_user(user_id):
                    interaction_stats['total'] += 1
                
                if i % 100 == 0:
                    update.message.reply_text(
                        f"⏳ تقدم العمل: تفاعل مع {i} متابع\n"
                        f"آخر حساب: {user_id}",
                        reply_markup=KEYBOARD_RUNNING
                    )
                    time.sleep(20)
                    
    except Exception as e:
        update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
    finally:
        if not stop_event.is_set():
            update.message.reply_text(
                "✅ اكتملت جميع التفاعلات!\n"
                "اضغط ▶️ تشغيل البوت لبدء جلسة جديدة",
                reply_markup=KEYBOARD_MAIN
            )

def main():
    updater = Updater(config.BOT_TOKEN)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    updater.start_polling(timeout=30, drop_pending_updates=True)
    print("✅ البوت يعمل الآن...")
    updater.idle()

if __name__ == "__main__":
    main()
