from instagrapi import Client
from instagrapi.exceptions import TwoFactorRequired
import time

class InstagramBot:
    def __init__(self):
        self.cl = Client()
    
    def login(self, username, password, verification_code=None):
        try:
            if verification_code:
                self.cl.login(username, password, verification_code=verification_code)
            else:
                self.cl.login(username, password)
            return True
        except TwoFactorRequired:
            return "need_verification"
        except Exception as e:
            return f"error: {str(e)}"
    
    def interact_with_followers(self, target_accounts, stop_event):
        for target in target_accounts:
            followers = self.cl.user_followers(target, amount=1000)
            for i, (user_id, _) in enumerate(followers.items(), 1):
                if stop_event.is_set():
                    return "stopped"
                
                try:
                    stories = self.cl.user_stories(user_id)
                    if stories:
                        self.cl.story_like(stories[0].id)
                        print(f"تم التفاعل مع قصة {user_id}")
                except Exception as e:
                    print(f"خطأ في {user_id}: {str(e)}")
                
                if i % 100 == 0:
                    time.sleep(20)