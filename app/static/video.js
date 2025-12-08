console.log("✅ video.js loaded");

const SIGNALING_SERVER = window.location.origin.replace('http', 'ws');
const socket = io(SIGNALING_SERVER, { transports: ["websocket"] });

const urlParams = new URLSearchParams(window.location.search);
let room = urlParams.get("room") || null;
const isViewer = !!room;

let mediaStream = null;
let peerConnections = {};
let isStreaming = false;
let mediaRecorder, recordedChunks = [], recInterval, recSeconds = 0;
let liveInterval, liveSeconds = 0;

let ICE_CONFIG = { iceServers: [] };


async function loadIceServers() {
  try {
    const res = await fetch("/api/turnservers");
    const data = await res.json();
    ICE_CONFIG = { iceServers: data.iceServers };
    console.log("✅ Loaded dynamic ICE config:", ICE_CONFIG);
  } catch (err) {
    console.error("❌ Failed to load ICE config, using fallback");
    ICE_CONFIG = {
      iceServers: [
        { urls: "stun:stun.l.google.com:19302" }
      ]
    };
  }
}

loadIceServers();


// to load recorded videos
async function loadRecordings() {
  try {
    const res = await fetch("/api/recordings");
    const files = await res.json();

    const container = document.getElementById("recordings");
    container.innerHTML = "";

    files.forEach(file => {
      const wrapper = document.createElement("div");
      wrapper.className = "recording-wrapper";

      const video = document.createElement("video");
      video.controls = true;
      video.src = `/api/recordings/${file}`;
      video.className = "recording-video";

      const overlay = document.createElement("div");
      overlay.className = "recording-overlay";

      const delBtn = document.createElement("button");
      delBtn.className = "overlay-btn";
      delBtn.innerHTML = `<i class="fas fa-trash"></i>`;
      delBtn.onclick = () => deleteRecording(file);  // implement this function if not yet

      const fsBtn = document.createElement("button");
      fsBtn.className = "overlay-btn";
      fsBtn.innerHTML = `<i class="fas fa-expand"></i>`;
      fsBtn.onclick = () => video.requestFullscreen();

      overlay.appendChild(delBtn);
      overlay.appendChild(fsBtn);
      wrapper.appendChild(video);
      wrapper.appendChild(overlay);

      container.appendChild(wrapper);
    });
  } catch (err) {
    console.error("❌ Failed to load recordings:", err);
  }
}


function deleteRecording(filename) {
  if (!confirm("Are you sure you want to delete this recording?")) return;

  fetch(`/api/recordings/${filename}`, {
    method: "DELETE"
  })
    .then(res => {
      if (!res.ok) throw new Error("Failed to delete recording");
      loadRecordings(); // reload list after delete
    })
    .catch(err => {
      console.error("❌ Could not delete recording:", err);
      alert("Error deleting recording");
    });
}

// prepare data for snapshot
function uploadSnapshot(base64Img) {
  const now = new Date();
  const payload = {
    hospital_id: 1,
    uid: "default-mf",
    visit_id: 1,
    procedure_id: 0,
    procedure_datetime: now.toISOString(),
    file_type: "image/png",
    file_status: "main",
    annotation_data: "",
    Img: base64Img,  // base64 image
    filename: `snapshot_${now.getTime()}.png`  // optional filename
  };

  fetch("/api/save-snapshots/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
    .then(async res => {
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text);
      }
      return res.json();
    })
    .then(data => {
      console.log("📸 Snapshot uploaded:", data);
      loadSnapshots(); // Refresh sidebar
    })
    .catch(err => {
      console.error("❌ Snapshot upload failed:", err);
      alert("Snapshot upload failed.");
    });
}


/* Document Events */
document.addEventListener("DOMContentLoaded", () => {
  if (isViewer) {
    socket.emit("join", { room, broadcaster: false });
    socket.emit("viewer_ready", { room });  // emit room to server
    document.body.classList.add("viewer-only");
  } else {
    const select = document.getElementById("deviceSelect");
    navigator.mediaDevices.enumerateDevices().then(devices => {
      select.innerHTML = '<option value="">Select Device</option>';
      devices.filter(d => d.kind === 'videoinput').forEach(device => {
        const opt = document.createElement('option');
        opt.value = device.deviceId;
        opt.text = device.label || `Camera ${device.deviceId}`;
        select.appendChild(opt);
      });
    });
    loadRecordings();  // ✅ to load recordings
    loadSnapshots();  // to load snapshots
  }
});

function formatTime(sec) {
  const m = Math.floor(sec / 60).toString().padStart(2, '0');
  const s = (sec % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

function toggleStream() {
  const video = document.getElementById("localVideo");
  const img = document.getElementById("defaultImage");
  const btn = document.getElementById("startBtn");
  const icon = btn.querySelector("i");
  const deviceId = document.getElementById("deviceSelect")?.value;

  if (!isStreaming) {
    if (!deviceId) return alert("Please select a device first.");

    navigator.mediaDevices.getUserMedia({ video: { deviceId: { exact: deviceId } }, audio: true })
      .then(stream => {
        mediaStream = stream;
        video.srcObject = stream;
        video.controls = false;
        document.getElementById("generateLinkBtn").disabled = false;
        document.getElementById("snapshotBtn").disabled = false;
        document.querySelector('.video-controls').style.display = 'flex';
        document.getElementById("recordBtn").disabled = false;
        document.getElementById("liveBadge").style.display = 'flex';
        img.style.display = "none";
        document.querySelector('.overlay').style.display = 'flex';
        icon.className = "fas fa-pause";
        isStreaming = true;

        if (!room) room = deviceId + '-' + Math.random().toString(36).substr(2, 5);

        socket.emit("join", { room, broadcaster: true });

        liveSeconds = 0;
        clearInterval(liveInterval);
        liveInterval = setInterval(() => {
          liveSeconds++;
          document.getElementById("liveLabel").textContent = `LIVE • ${formatTime(liveSeconds)}`;
          document.getElementById("customProgress").style.width = `${(liveSeconds % 60) * (100 / 60)}%`;
        }, 1000);
      })
      .catch(err => {
        console.error("❌ Media access error:", err);
        alert("Unable to start stream.");
      });
  } else {
    mediaStream.getTracks().forEach(track => track.stop());
    video.srcObject = null;
    isStreaming = false;
    clearInterval(liveInterval);

    document.getElementById("generateLinkBtn").disabled = true;
    document.getElementById("snapshotBtn").disabled = true;
    document.getElementById("recordBtn").disabled = true;
    document.getElementById("liveBadge").style.display = 'none';
    document.querySelector('.overlay').style.display = 'none';
    img.style.display = "block";
    icon.className = "fas fa-play";
    document.getElementById("customProgress").style.width = '0%';
  }
}

function toggleRecording() {
  const recBadge = document.getElementById("recBadge");
  const recordBtn = document.getElementById("recordBtn");
  const stream = document.getElementById("localVideo").srcObject;

  if (!mediaRecorder || mediaRecorder.state === 'inactive') {
    recSeconds = 0;
    recordedChunks = [];
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = e => recordedChunks.push(e.data);

    mediaRecorder.onstop = () => {
      const blob = new Blob(recordedChunks, { type: 'video/webm' });
      const formData = new FormData();
      formData.append("video", blob, `rec_${Date.now()}.webm`);

      fetch("/api/save-recording", { method: "POST", body: formData })
        .then(res => res.json())
        .then(data => {
          console.log("📤 Uploaded recording", data);
          loadRecordings(); // <-- reload UI with new video
        });
    };

    mediaRecorder.start();
    recBadge.style.display = 'flex';
    recInterval = setInterval(() => {
      recSeconds++;
      document.getElementById("recLabel").textContent = `REC • ${formatTime(recSeconds)}`;
      document.getElementById("recProgress").style.width = `${(recSeconds % 60) * (100 / 60)}%`;
    }, 1000);

    recordBtn.classList.add("recording-active");
    recordBtn.innerHTML = '<i class="fas fa-stop"></i>';
  } else {
    mediaRecorder.stop();
    clearInterval(recInterval);
    recBadge.style.display = 'none';
    document.getElementById("recProgress").style.width = '0%';
    recordBtn.classList.remove("recording-active");
    recordBtn.innerHTML = '<i class="fas fa-circle"></i>';
  }
}
async function loadSnapshots() {
  try {
    const res = await fetch("/api/snapshots/");
    const data = await res.json();

    const container = document.getElementById("snapshots");
    container.innerHTML = "";

    (data.mediafiles || []).forEach(snapshot => {
      const wrapper = document.createElement("div");
      wrapper.className = "snapshot-wrapper";

      const img = document.createElement("img");
      img.src = `${location.origin}${snapshot.file_src}`;
      img.className = "snapshot-img";

      const overlay = document.createElement("div");
      overlay.className = "snapshot-overlay";

      const delBtn = document.createElement("button");
      delBtn.className = "overlay-btn";
      delBtn.title = "Delete";
      delBtn.innerHTML = `<i class="fas fa-trash-alt"></i>`;
      delBtn.onclick = () => deleteSnapshot(snapshot.id);

      const fsBtn = document.createElement("button");
      fsBtn.className = "overlay-btn";
      fsBtn.title = "Fullscreen";
      fsBtn.innerHTML = `<i class="fas fa-expand"></i>`;
      fsBtn.onclick = () => img.requestFullscreen();

      overlay.appendChild(delBtn);
      overlay.appendChild(fsBtn);
      wrapper.appendChild(img);
      wrapper.appendChild(overlay);
      container.appendChild(wrapper);
    });
  } catch (err) {
    console.error("❌ Failed to load snapshots:", err);
  }
}


function deleteSnapshot(id) {
  fetch(`/api/snapshots/?id=${id}`, { method: "DELETE" })
    .then(res => res.json())
    .then(data => {
      console.log("🗑️ Deleted:", data);
      loadSnapshots();
    })
    .catch(err => {
      console.error("❌ Delete failed:", err);
      alert("Failed to delete snapshot.");
    });
}


function captureSnapshot() {
  const video = document.getElementById("localVideo");
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext("2d").drawImage(video, 0, 0);

  const base64Img = canvas.toDataURL("image/png");

  // Show in UI
  const img = document.createElement("img");
  img.src = base64Img;
  img.style.width = "100%";
  document.getElementById("snapshots").prepend(img);

  // Upload to server
  uploadSnapshot(base64Img);
}


socket.on("offer", async ({ from, offer }) => {
  const pc = new RTCPeerConnection(ICE_CONFIG);
  peerConnections[from] = pc;

  pc.ontrack = (e) => {
    const video = document.getElementById("localVideo");
    if (!video.srcObject || video.srcObject.id !== e.streams[0].id) video.srcObject = e.streams[0];
  };

  pc.onconnectionstatechange = () => console.log("Peer state:", pc.connectionState);
  await pc.setRemoteDescription(new RTCSessionDescription(offer));
  const answer = await pc.createAnswer();
  await pc.setLocalDescription(answer);
  socket.emit("answer", { to: from, answer });
});

socket.on("answer", async ({ from, answer }) => {
  const pc = peerConnections[from];
  if (pc) await pc.setRemoteDescription(new RTCSessionDescription(answer));
});

socket.on("viewer-ready", ({ viewer_id }) => {
  if (!isViewer && mediaStream) {
    const pc = new RTCPeerConnection(ICE_CONFIG);
    peerConnections[viewer_id] = pc;
    mediaStream.getTracks().forEach(track => pc.addTrack(track, mediaStream));
    pc.onicecandidate = e => e.candidate && socket.emit("candidate", { to: viewer_id, candidate: e.candidate });
    pc.createOffer().then(offer => {
      pc.setLocalDescription(offer);
      socket.emit("offer", { to: viewer_id, offer });
    });
  }
});

socket.on("candidate", ({ from, candidate }) => {
  const pc = peerConnections[from];
  if (pc && candidate) pc.addIceCandidate(new RTCIceCandidate(candidate));
});

function toggleFullscreen() {
  const vc = document.querySelector(".video-grid");
  if (!document.fullscreenElement) vc.requestFullscreen();
  else document.exitFullscreen();
}

function showTab(tabId) {
  document.querySelectorAll('.tab-pane').forEach(p => p.style.display = 'none');
  document.getElementById(tabId).style.display = 'flex';
  document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
  const idx = { snapshots: 0, recordings: 1 }[tabId];
  if (idx !== undefined) document.querySelectorAll('.tab-button')[idx].classList.add('active');
}

// Generate Shareable Link
if (!isViewer) {
  document.getElementById("generateLinkBtn").addEventListener("click", () => {
    if (!room) {
      const deviceId = document.getElementById("deviceSelect").value;
      room = deviceId + '-' + Math.random().toString(36).substr(2, 5);
    }
    const link = `${window.location.origin}/video?room=${room}`;
    navigator.clipboard.writeText(link).then(() => alert("Link copied to clipboard!"));
  });



}
