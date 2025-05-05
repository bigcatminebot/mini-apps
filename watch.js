const videoIds = [
  "pw4LdlA9bkU", "xDAZZW5Kbiw", "3L4Qcq07LCY",
  "6Y_VaEjhCG0E", "tFXamlMwbqY", "1nj9_hMuvlk",
  "cS_TtyMvTMs", "MzKpGbYFhhc"
];

let player;
let countdown = 60;
let timer = null;
let isWatched = false;
let isCounting = false;
let dailyLimit = 10;
let completed = 0;

function updateMissionCount() {
  const remaining = dailyLimit - completed;
  document.getElementById("missionCount").textContent =
    remaining > 0
      ? `Misi tersisa hari ini: ${remaining}`
      : "🎉 Kamu telah menyelesaikan semua misi hari ini!";
}

function getRandomVideoId() {
  const index = Math.floor(Math.random() * videoIds.length);
  return videoIds[index];
}

function onYouTubeIframeAPIReady() {
  const initialVideo = getRandomVideoId();
  player = new YT.Player('player', {
    height: '405',
    width: '100%',
    videoId: initialVideo,
    events: {
      'onReady': onPlayerReady,
      'onStateChange': onPlayerStateChange
    }
  });
}

function onPlayerReady(event) {
  player.mute();
}

function startWatching() {
  if (completed >= dailyLimit) return;

  const videoId = getRandomVideoId();
  countdown = 60;
  isWatched = false;
  isCounting = false;

  const button = document.getElementById("watchButton");
  button.disabled = true;
  button.textContent = `Menonton... (${countdown} detik)`;

  player.mute();
  player.loadVideoById(videoId);
  player.playVideo();
}

function onPlayerStateChange(event) {
  const button = document.getElementById("watchButton");

  if (event.data === YT.PlayerState.PLAYING && !isWatched) {
    if (!isCounting) {
      isCounting = true;
      timer = setInterval(() => {
        countdown--;
        button.textContent = `Menonton... (${countdown} detik)`;
        if (countdown <= 0) {
          clearInterval(timer);
          isWatched = true;
          isCounting = false;
          button.textContent = "✅ Klaim Reward";
          button.disabled = false;
          button.onclick = claimReward;
        }
      }, 1000);
    }
  } else if (event.data === YT.PlayerState.PAUSED || event.data === YT.PlayerState.ENDED) {
    if (isCounting) {
      clearInterval(timer);
      isCounting = false;
    }
  }
}

function claimReward() {
  if (!isWatched || completed >= dailyLimit) return;

  const reward = Math.floor(Math.random() * (25 - 10 + 1)) + 10;

  // Call Monetag rewarded ad before giving reward
  showRewardedAd(() => {
    alert(`🎉 Kamu mendapatkan Rp${reward}!\nSilahkan screenshot halaman ini untuk melakukan penarikan!`);

    completed++;
    updateMissionCount();

    const button = document.getElementById("watchButton");
    if (completed < dailyLimit) {
      button.textContent = "Tonton Misi Berikutnya";
      button.onclick = startWatching;
      button.disabled = false;
    } else {
      button.textContent = "✅ Semua Misi Selesai";
      button.disabled = true;
    }
  });
}

updateMissionCount();
