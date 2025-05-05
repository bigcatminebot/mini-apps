// Tampilkan rewarded ad dan jalankan callback jika selesai
function showRewardedAd(onComplete) {
  if (typeof show_9293871 === 'function') {
    show_9293871().then(() => {
      onComplete(); // lanjutkan reward setelah ad selesai
    }).catch(() => {
      alert("Gagal memuat iklan. Coba lagi.");
      onComplete(); // tetap berikan reward jika iklan gagal, atau bisa dibatalkan
    });
  } else {
    console.warn("Monetag tidak tersedia.");
    onComplete(); // fallback
  }
}

// Optional: Interstitial ad otomatis
if (typeof show_9293871 === 'function') {
  show_9293871({
    type: 'inApp',
    inAppSettings: {
      frequency: 2,
      capping: 0.1,
      interval: 30,
      timeout: 5,
      everyPage: false
    }
  });
}
