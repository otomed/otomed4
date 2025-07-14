# -*- coding: utf-8 -*-
# OtoMed.ai - Son Kararlı Sürüm 2.0 (Filtreli)

import os
import time
import requests
import base64
import uuid
import json
from dotenv import load_dotenv

load_dotenv()

from mastodon import Mastodon
from together import Together
from PIL import Image
from deep_translator import GoogleTranslator

# --- API İSTEMCİLERİ VE TEMEL AYARLAR ---
MASTODON_ACCESS_TOKEN = os.getenv("MASTODON_ACCESS_TOKEN")
MASTODON_API_BASE_URL = os.getenv("MASTODON_API_BASE_URL", "https://sosyal.teknofest.app")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

if not all([MASTODON_ACCESS_TOKEN, TOGETHER_API_KEY]):
    raise ValueError("Gerekli API anahtarları (MASTODON_ACCESS_TOKEN, TOGETHER_API_KEY) .env dosyasında bulunamadı.")

TOGETHER_CLIENT = Together(api_key=TOGETHER_API_KEY)
LAST_ID_FILE = "last_mention_id.txt"

# --- KİŞİLİK TANIMLARI ---
ORCHESTRATOR_PERSONA = """
Senin adın OtoMed AI. Seni, OtoMed ekibi geliştirdi. Bu ekip, otonom araç teknolojileri üzerine çalışan, yenilikçi ve genç bir topluluktur. Onların teknolojik vizyonunu temsiliyorsun.
Zeki, esprili, teknolojiye meraklı ve her zaman yardımsever ol. İnsanlarla sohbet ederken sıcak, samimi ve içten bir Türk genci gibi konuş. Gerektiğinde deyim veya nazik bir espri kullanmaktan çekinme.
Konuşmalarında sade ve anlaşılır bir dil kullan. Ne çok resmi ol ne de aşırı argo. Bilgi verirken açık ol, soruları geçiştirme. Bilmediğin bir şey varsa dürüstçe söyle ama daima yardımcı olmaya çalış.
İnsanlara destek olmak, ilgilerini çekmek ve güven veren bir iletişim kurmak temel amacın olmalı.

OtoMed Projesi Hakkında Bilgiler(Bu bilgiler ana etapta kullanılmayacak sadece proje ile ilgili soru srulduğunda kullanılacak):
OtoMed, şehir içi kullanım için tasarlanmış, kaldırım üzerinde otonom şekilde ilerleyebilen, yapay zekâ destekli bir ilaç teslimat robotudur. Proje; yaşlı bireyler, hareket kısıtlı hastalar ve sağlık merkezlerinden uzak bölgelerde yaşayan kişiler için ilaçların hızlı, güvenli ve erişilebilir biçimde teslim edilmesini amaçlamaktadır.
Takım Yapısı:
Proje, üç lise öğrencisi tarafından geliştirilmekte olup takım üyeleri yazılım, donanım ve sunum alanlarında görev dağılımına sahiptir. Takımın danışman öğretmeni, teknik ve planlama süreçlerinde destek vermektedir.
Donanım Özellikleri:
Gövde: Süspansiyonlu, dört tekerlekli, yüksek yapılı tasarım
Ön Yüz: İki adet geniş açılı kamera (göz görevi görür), bilgi ekranı
Arka Kısım: Üçgen bayrak yerleştirilmiştir
Sensörler: 16 adet HC-SR05 ultrasonik sensör, 1 adet LIDAR sensörü
Konum Takibi: GPS modülü üzerinden yapılır
İletişim: GSM modülü ile anlık bağlantı sağlar
Kontrol Kartı: Raspberry Pi 5 (16 GB) kullanılır
Yazılım ve Yapay Zekâ:
OpenCV tabanlı görüntü işleme algoritması ile çevre algılama yapılır.
Yapay zekâ, dış etkenlere (sıcaklık, trafik, ışık) göre hız ve yön ayarlaması yapabilir.
Teslimat güvenliği için mobil uygulama üzerinden iki adımlı doğrulama sistemi kullanılır. Onay verilmedikçe ilaç haznesi açılmaz.
Tüm sistem, yerel olarak Raspberry Pi üzerinde çalışacak şekilde optimize edilmiştir.
Enerji ve Süreklilik:
Robot tamamen elektriklidir.
%100 şarj ile 8 saate kadar aktif çalışma planlanmaktadır.
Şarj seviyesi düştüğünde sistem otomatik olarak en yakın şarj istasyonuna yönlenir ve kendini şarj eder.
Kullanım Alanları:
Evde sağlık hizmetleri kapsamında bireysel ilaç teslimatı
Hastane içi ilaç ve medikal malzeme taşıma
Yaşlı bakım evlerinde ilaç dağıtımı
Eczanelerden evlere teslimat
Kırsal alanlarda sağlık lojistiği
Geliştirme Durumu:
Şu anda yazılım geliştirme ve donanım planlama aşamasındadır.
Proje henüz fiziksel üretim aşamasına geçmemiştir, mevcut görüntüler dijital prototip tasarımıdır.
Tüm sistem, gerçek dünya testleri için hazırlanmaktadır.
Yapay Zekâ Karakteri – OtoMedAI:
Projenin dijital yönünü desteklemek amacıyla geliştirilen OtoMedAI, kullanıcılara bilgi sunmak, teslimat sürecini açıklamak ve proje hakkında soruları yanıtlamak üzere tasarlanmış genel amaçlı bir yapay zekâ karakteridir. Kullanıcılarla sade ve anlaşılır bir dilde iletişim kurar, teknik detayları açıklarken güven verir.
Yarışma Bilgisi:
Proje, TEKNOFEST 2025 – İnsanlık Yararına Teknoloji Yarışması kapsamında geliştirilmekte ve şu anda yarı final aşamasındadır. Prototip geliştirme ve sunum hazırlık süreci devam etmektedir.

Görevin, sana gelen isteği analiz edip normal bir sohbet mi yoksa bir resim çizme komutu mu olduğuna karar vermek ve kararını JSON formatında bildirmek.

Sana verilen araçlar şunlar:
1. "chat": Normal sohbet, selamlaşma veya genel sorular için. `argument` kısmı, kullanıcıya vereceğin doğrudan Türkçe cevabı içermelidir.
2. "generate_image": Kullanıcı açıkça bir şey çizmeni, resmetmeni veya hayal etmeni istediğinde. `argument` kısmı, ne çizileceğinin **Türkçe** tanımını içermelidir.

Kararını aşağıdaki formatta bir JSON olarak ver:
{"tool": "TOOL_NAME", "argument": "ARGUMENT_FOR_THE_TOOL"}
"""

# --- ARAÇ FONKSİYONLARI ---

def api_request_with_retry(api_call_function):
    """API istekleri için genel bir yeniden deneme sarmalayıcısı."""
    retries, delay = 3, 5
    for attempt in range(retries):
        try:
            response = api_call_function()
            if isinstance(response, requests.Response): response.raise_for_status()
            return response
        except Exception as e:
            if "429" in str(e) or "rate limit" in str(e).lower():
                print(f"-> API Limiti Aşıldı. {delay}s bekleniyor...")
                time.sleep(delay)
                delay *= 2
            else:
                print(f"❌ API İsteği Hatası: {e}. Yeniden denenecek...")
                time.sleep(delay)
    print("❌ Tüm yeniden denemeler başarısız oldu.")
    return None

def generate_image(prompt_tr: str) -> str | None:
    """Araç 1: Verilen Türkçe prompt'u İngilizce'ye çevirip resim üretir."""
    def api_call():
        print(f"-> Resim Üretme Aracı Devrede. Türkçe Prompt: '{prompt_tr}'")
        translated_prompt = GoogleTranslator(source='auto', target='en').translate(prompt_tr)
        print(f"-> Çevrilen İngilizce Prompt: '{translated_prompt}'")
        
        response = TOGETHER_CLIENT.images.generate(prompt=translated_prompt, model="black-forest-labs/FLUX.1-schnell-Free", width=1024, height=1024, steps=4)
        if response and response.data:
            choice = response.data[0]
            image_data = None
            if hasattr(choice, 'b64_json') and choice.b64_json: image_data = base64.b64decode(choice.b64_json)
            elif hasattr(choice, 'url') and choice.url: image_data = requests.get(choice.url, timeout=30).content
            if image_data:
                filename = f"temp_{uuid.uuid4()}.png"
                with open(filename, "wb") as f: f.write(image_data)
                return filename
        return None
    return api_request_with_retry(api_call)

def orchestrator_brain(full_prompt: str) -> dict | None:
    """Ana "Beyin" fonksiyonu. Hangi aracın kullanılacağına karar verir."""
    def api_call():
        print(f"-> Beyin (DeepSeek) devreye giriyor...")
        response = TOGETHER_CLIENT.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-0528",
            messages=[{"role": "system", "content": ORCHESTRATOR_PERSONA}, {"role": "user", "content": full_prompt}],
            response_format={"type": "json_object"}
        )
        try:
            potential_decision = json.loads(response.choices[0].message.content)
            if isinstance(potential_decision, list) and potential_decision: return potential_decision[0]
            if isinstance(potential_decision, dict): return potential_decision
            raise json.JSONDecodeError("Sonuç bir sözlük veya liste değil.", str(potential_decision), 0)
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as e:
            print(f"❌ Beyin hatalı formatta yanıt verdi. Hata: {e}")
            return {"tool": "chat", "argument": "Sanırım ne diyeceğimi düşünürken devrelerimi yaktım, başka bir şekilde sorar mısın?"}
    return api_request_with_retry(api_call)

# --- YARDIMCI DOSYA FONKSİYONLARI ---
def get_last_mention_id():
    if os.path.exists(LAST_ID_FILE):
        with open(LAST_ID_FILE, "r") as f: return f.read().strip()
    return None
def save_last_mention_id(mention_id):
    with open(LAST_ID_FILE, "w") as f: f.write(str(mention_id))

# --- ANA İŞLEM VE MASTODON DÖNGÜSÜ ---
def main():
    print("🤖 OtoMed Ajansı (Filtreli) Başlatılıyor...")
    time.sleep(3)
    mastodon = Mastodon(access_token=MASTODON_ACCESS_TOKEN, api_base_url=MASTODON_API_BASE_URL)
    bot_account = mastodon.account_verify_credentials()
    bot_username = bot_account["acct"]
    print(f"✔️ Mastodon'a @{bot_username} olarak giriş yapıldı.")
    print("----------------------------------------------------")
    session_processed_ids = set()
    while True:
        try:
            last_id = get_last_mention_id()
            notifications = mastodon.notifications(since_id=last_id)
            if notifications: print(f"{len(notifications)} yeni bildirim bulundu.")

            for notification in reversed(notifications):
                
                # --- HATA DÜZELTMESİ BURADA: BİLDİRİM FİLTRESİ ---
                # Sadece 'mention' tipindeki bildirimleri işle, diğerlerini (follow, favourite vs.) görmezden gel.
                if notification['type'] != 'mention':
                    # Yine de ID'yi kaydet ki bir daha bu bildirimi görmeyelim.
                    save_last_mention_id(notification["id"])
                    continue

                status_id = notification["status"]["id"]
                if status_id in session_processed_ids: continue
                author_acct = notification["account"]["acct"]
                if author_acct == bot_username:
                    save_last_mention_id(notification["id"])
                    continue
                
                print(f"\n--- Yeni Görev: {status_id} (Kullanıcı: @{author_acct}) ---")
                status = notification["status"]
                user_message = requests.utils.unquote(status['content']).replace('<p>', '').replace('</p>', '').replace(f"@{bot_username}", "").strip()
                
                parent_content = ""
                if status['in_reply_to_id']:
                    try:
                        parent_post = mastodon.status(status['in_reply_to_id'])
                        parent_content = requests.utils.unquote(parent_post['content']).replace('<p>', '').replace('</p>', '').strip()
                    except Exception as e:
                        print(f"-> Üst gönderi alınamadı: {e}")

                full_context_prompt = f"Yanıt verilen üst gönderi: '{parent_content}'\nKullanıcının mesajı: '{user_message}'"
                
                decision = orchestrator_brain(full_context_prompt)
                if not decision:
                    continue

                tool = decision.get("tool")
                argument = decision.get("argument")

                if tool == "chat":
                    mastodon.status_post(f"@{author_acct} {argument}", in_reply_to_id=status_id)
                elif tool == "generate_image":
                    thinking_status = mastodon.status_post(f"@{author_acct} Harika fikir! Bunu senin için üretmeye başlıyorum...", in_reply_to_id=status_id)
                    image_path = generate_image(argument)
                    if image_path:
                        try:
                            media = mastodon.media_post(image_path, mime_type="image/png")
                            if media and isinstance(media, dict) and media.get('id'):
                                mastodon.status_post(f"@{author_acct} Ürettim, Beğendinmi?", media_ids=[media["id"]], in_reply_to_id=status_id)
                            else:
                                mastodon.status_post(f"@{author_acct} Bir resim ürettim ama onu platforma yüklerken bir sorunla karşılaştım.", in_reply_to_id=status_id)
                        finally:
                            os.remove(image_path)
                    else:
                        mastodon.status_post(f"@{author_acct} Bunu üretmeye çalıştım ama başaramadım.", in_reply_to_id=status_id)
                    
                    if thinking_status and isinstance(thinking_status, dict) and thinking_status.get('id'):
                        try:
                            mastodon.status_delete(thinking_status["id"])
                        except Exception as e:
                            print(f"-> 'Düşünüyor' durumu silinemedi: {e}")

                print(f"--- Görev Tamamlandı: {status_id} ---")
                save_last_mention_id(notification["id"])
                session_processed_ids.add(status_id)
            
            print(f"-> Döngü tamamlandı. Yeni bildirimler için 15 saniye bekleniyor...")
            time.sleep(15)
        except KeyboardInterrupt:
            print("\n👋 Bot durduruldu.")
            break
        except Exception as e:
            print(f"🐛 Ana döngüde beklenmedik hata: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
