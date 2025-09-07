#!/usr/bin/env bash
set -e

# Basit script: release-keystore.jks oluşturur, base64'e çevirir ve ekleme talimatı verir.
# Kullanım: ./create-keystore.sh
# Gereksinim: keytool (JDK) ve base64 (çoğu Unix sisteminde var)

KEYSTORE_FILE="release-keystore.jks"
ALIAS="snake_key"
DNAME="CN=Yasin,O=Yasin0023,C=TR"
VALIDITY_DAYS=10000
KEYALG="RSA"
KEYSIZE=2048

if [ -f "$KEYSTORE_FILE" ]; then
  echo "Hata: $KEYSTORE_FILE zaten mevcut. Yedeğini alın veya farklı bir isim kullanın."
  exit 1
fi

echo "Keystore oluşturuluyor: $KEYSTORE_FILE"
keytool -genkeypair \
  -alias "$ALIAS" \
  -keyalg "$KEYALG" \
  -keysize "$KEYSIZE" \
  -validity "$VALIDITY_DAYS" \
  -keystore "$KEYSTORE_FILE" \
  -dname "$DNAME"

echo
echo "Keystore oluşturuldu: $KEYSTORE_FILE"
echo "Şimdi base64 olarak çıktı alınıyor (GitHub Secret olarak eklemeniz için)."
echo "------- BEGIN BASE64 (copy this whole block into a GitHub Secret named KEYSTORE_BASE64) -------"
base64 "$KEYSTORE_FILE"
echo "-------- END BASE64 --------"
echo
echo "NOTLAR:"
echo "1) GitHub repo ayarlarına (Settings -> Secrets) aşağıdaki secrets'i ekleyin:"
echo "   - KEYSTORE_BASE64   (buraya yukarıdaki base64 çıktısını yapıştırın)"
echo "   - STORE_PASSWORD    (keystore oluştururken verdiğiniz password)"
echo "   - KEY_ALIAS         (default: $ALIAS)"
echo "   - KEY_PASSWORD      (anahtar şifresi, genelde STORE_PASSWORD ile aynı olabilir)"
echo "2) Keystore dosyasını repoya commit etmeyin. release-keystore.jks'yi güvenli yerde saklayın."
echo "3) Public sertifikayı dışa aktarmak isterseniz:"
echo "   keytool -export -rfc -keystore $KEYSTORE_FILE -alias $ALIAS -file snake_cert.pem"