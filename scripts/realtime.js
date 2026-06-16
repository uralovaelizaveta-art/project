class RealtimeController {
  constructor() {
    this.modal = document.getElementById('realtimeModal');
    this.realtimeButton = document.getElementById('realtimeButton');
    this.realtimeCloseBtn = document.getElementById('realtimeCloseBtn');

    this.video = document.getElementById('videoElement');
    this.poseOverlay = document.getElementById('poseOverlay');
    this.poseCtx = this.poseOverlay ? this.poseOverlay.getContext('2d') : null;
    this.canvas = null;
    this.ctx = null;
    this.stream = null;
    this.ws = null;
    this.isConnecting = false;
    this.waitingForResult = false;
    this.isRunning = false;
    this.isSkeletonVisible = true;
    this.frameCount = 0;
    this.startTime = Date.now();
    this.frameIntervalMs = 50;
    this.frameWidth = 384;
    this.frameHeight = 288;
    this.lastProcessingMs = null;
    this.movements = [];
    this.maxMovements = 20;
    this.poseConnections = [
      ['left_shoulder', 'right_shoulder'],
      ['left_shoulder', 'left_elbow'],
      ['left_elbow', 'left_wrist'],
      ['right_shoulder', 'right_elbow'],
      ['right_elbow', 'right_wrist'],
      ['left_shoulder', 'left_hip'],
      ['right_shoulder', 'right_hip'],
      ['left_hip', 'right_hip'],
      ['left_hip', 'left_knee'],
      ['left_knee', 'left_ankle'],
      ['right_hip', 'right_knee'],
      ['right_knee', 'right_ankle'],
      ['left_ankle', 'left_heel'],
      ['left_heel', 'left_foot_index'],
      ['left_ankle', 'left_foot_index'],
      ['right_ankle', 'right_heel'],
      ['right_heel', 'right_foot_index'],
      ['right_ankle', 'right_foot_index']
    ];

    this.startBtn = document.getElementById('startBtn');
    this.stopBtn = document.getElementById('stopBtn');
    this.toggleSkeletonBtn = document.getElementById('toggleSkeletonBtn');
    this.statusText = document.getElementById('statusText');
    this.statusIndicator = document.getElementById('statusIndicator');
    this.movementsList = document.getElementById('movementsList');
    this.fpsCounter = document.getElementById('fpsCounter');
    this.currentMovementName = document.getElementById('currentMovementName');
    this.currentMovementConfidence = document.getElementById('currentMovementConfidence');

    this.setupEventListeners();
  }

  setupEventListeners() {
    this.realtimeButton.addEventListener('click', () => this.openModal());
    this.realtimeCloseBtn.addEventListener('click', () => this.closeModal());
    this.modal.addEventListener('click', (e) => {
      if (e.target === this.modal) this.closeModal();
    });

    this.startBtn.addEventListener('click', () => this.start());
    this.stopBtn.addEventListener('click', () => this.stop());
    if (this.toggleSkeletonBtn) {
      this.toggleSkeletonBtn.addEventListener('click', () => this.toggleSkeleton());
    }
  }

  openModal() {
    this.modal.classList.add('active');
  }

  closeModal() {
    this.stop();
    this.modal.classList.remove('active');
  }

  async start() {
    try {
      this.startBtn.disabled = true;
      this.updateStatus('Запрашиваю доступ к камере...', false);

      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        }
      });

      this.video.srcObject = this.stream;
      this.video.muted = true;
      await new Promise(resolve => {
        this.video.onloadedmetadata = resolve;
      });
      await this.video.play();
      this.resizePoseOverlay();

      this.setupWebSocket();
      this.isRunning = true;
      this.stopBtn.disabled = false;
      this.updateStatus('Подключено. Отправляю кадры...', true);
      this.frameCount = 0;
      this.startTime = Date.now();

      this.processFrames();
    } catch (error) {
      console.error('Ошибка доступа к камере:', error);
      this.updateStatus('Ошибка доступа к камере. Проверьте разрешения.', false);
      this.startBtn.disabled = false;
    }
  }

  setupWebSocket() {
    if (this.isConnecting || (this.ws && (
      this.ws.readyState === WebSocket.OPEN ||
      this.ws.readyState === WebSocket.CONNECTING
    ))) {
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    let wsUrl;

    // Если на порту 8000 (HTTP сервер), то WebSocket на 8001 (FastAPI)
    if (window.location.port === '8000' || window.location.port === '') {
      wsUrl = `${protocol}//${window.location.hostname}:8001/ws`;
    } else {
      wsUrl = `${protocol}//${window.location.host}/ws`;
    }

    console.log('Connecting to WebSocket:', wsUrl);

    try {
      this.isConnecting = true;
      this.ws = new WebSocket(wsUrl);
    } catch (error) {
      this.isConnecting = false;
      console.error('WebSocket creation failed:', error);
      this.updateStatus('Ошибка: не удалось создать WebSocket', false);
      return;
    }

    this.ws.onopen = () => {
      this.isConnecting = false;
      console.log('WebSocket подключен');
      this.updateStatus('Подключено к серверу', true);
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.waitingForResult = false;
        if (data.type === 'result') {
          this.handleResult(data.data);
        } else if (data.type === 'error') {
          console.error('Server error:', data.message);
          this.updateStatus(`Ошибка сервера: ${data.message}`, false);
        }
      } catch (e) {
        console.error('Failed to parse message:', e);
      }
    };

    this.ws.onerror = (error) => {
      this.isConnecting = false;
      console.error('WebSocket ошибка:', error);
      this.updateStatus('Ошибка соединения с сервером', false);
    };

    this.ws.onclose = (event) => {
      this.isConnecting = false;
      this.waitingForResult = false;
      console.log('WebSocket отключен:', event.code, event.reason);
      if (this.isRunning) {
        this.updateStatus('Соединение потеряно. Переподключение...', false);
        setTimeout(() => this.setupWebSocket(), 2000);
      }
    };
  }

  processFrames() {
    if (!this.isRunning) return;

    if (!this.canvas) {
      this.canvas = document.createElement('canvas');
      this.canvas.width = this.frameWidth;
      this.canvas.height = this.frameHeight;
      this.ctx = this.canvas.getContext('2d');
    }

    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      if (!this.ws || this.ws.readyState === WebSocket.CLOSED) {
        this.setupWebSocket();
      }
      setTimeout(() => this.processFrames(), this.frameIntervalMs);
      return;
    }

    if (this.waitingForResult) {
      setTimeout(() => this.processFrames(), this.frameIntervalMs);
      return;
    }

    this.drawProcessingFrame();
    this.waitingForResult = true;
    this.canvas.toBlob((blob) => {
      if (!blob) {
        this.waitingForResult = false;
        console.warn('Canvas to blob failed');
        return;
      }

      try {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          this.ws.send(blob);
        } else {
          this.waitingForResult = false;
        }
      } catch (e) {
        this.waitingForResult = false;
        console.error('Failed to send frame:', e);
      }
    }, 'image/jpeg', 0.6);

    this.frameCount++;
    this.updateFPS();

    setTimeout(() => this.processFrames(), this.frameIntervalMs);
  }

  handleResult(result) {
    this.lastProcessingMs = result.processing_ms || null;
    const movement = result.movement || 'Не определено';
    const confidence = ((result.confidence || 0) * 100).toFixed(1);

    this.updateStatus(`Сейчас: ${movement} (${confidence}%)`, true);
    this.currentMovementName.textContent = movement;
    this.currentMovementConfidence.textContent = `${confidence}%`;
    if (result.ready_for_detection === false && Object.keys(result.pose_points || {}).length > 0) {
      this.updateStatus('Отойдите назад, чтобы фигура была видна полностью', true);
      this.currentMovementName.textContent = movement;
      this.currentMovementConfidence.textContent = 'Встаньте в полный рост';
    }
    this.drawPose(result.pose_points || {});

    if (Array.isArray(result.movements)) {
      this.movements = [...result.movements].reverse().map((item, index) => ({
        id: `${item.movement_id}-${item.time_sec}-${index}`,
        movementId: item.movement_id,
        movement: item.movement_name,
        confidence: ((item.confidence || 0) * 100).toFixed(1),
        timestamp: `${item.time_sec} с`
      }));
      this.renderMovements();
    }
  }

  renderMovements() {
    if (this.movements.length === 0) {
      this.movementsList.innerHTML = '<div class="empty-message">Движения будут отображены здесь...</div>';
      return;
    }

    this.movementsList.innerHTML = this.movements.map(m =>
      `<a class="movement-item" href="movement.html?id=${encodeURIComponent(m.movementId)}">
        <div>
          <div class="movement-name">${m.movement}</div>
          <small style="color: #999;">${m.timestamp}</small>
        </div>
        <div class="movement-confidence">${m.confidence}%</div>
      </a>`
    ).join('');
  }

  drawProcessingFrame() {
    const sourceWidth = this.video.videoWidth;
    const sourceHeight = this.video.videoHeight;
    if (!sourceWidth || !sourceHeight) return;

    const targetAspect = this.frameWidth / this.frameHeight;
    const sourceAspect = sourceWidth / sourceHeight;
    let sourceX = 0;
    let sourceY = 0;
    let cropWidth = sourceWidth;
    let cropHeight = sourceHeight;

    if (sourceAspect > targetAspect) {
      cropWidth = sourceHeight * targetAspect;
      sourceX = (sourceWidth - cropWidth) / 2;
    } else if (sourceAspect < targetAspect) {
      cropHeight = sourceWidth / targetAspect;
      sourceY = (sourceHeight - cropHeight) / 2;
    }

    this.ctx.drawImage(
      this.video,
      sourceX,
      sourceY,
      cropWidth,
      cropHeight,
      0,
      0,
      this.frameWidth,
      this.frameHeight
    );
  }

  resizePoseOverlay() {
    const width = this.video.clientWidth;
    const height = this.video.clientHeight;
    if (!this.poseOverlay || !this.poseCtx || !width || !height) return;

    const pixelRatio = window.devicePixelRatio || 1;
    const canvasWidth = Math.round(width * pixelRatio);
    const canvasHeight = Math.round(height * pixelRatio);
    if (
      this.poseOverlay.width === canvasWidth &&
      this.poseOverlay.height === canvasHeight
    ) {
      return;
    }

    this.poseOverlay.width = canvasWidth;
    this.poseOverlay.height = canvasHeight;
    this.poseCtx.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
  }

  clearPose() {
    if (!this.poseOverlay || !this.poseCtx) return;
    this.poseCtx.clearRect(
      0,
      0,
      this.video.clientWidth,
      this.video.clientHeight
    );
  }

  drawPose(points) {
    if (!this.isSkeletonVisible) {
      this.clearPose();
      return;
    }
    if (!this.poseOverlay || !this.poseCtx) return;
    this.resizePoseOverlay();
    this.clearPose();

    const width = this.video.clientWidth;
    const height = this.video.clientHeight;
    if (!width || !height || !Object.keys(points).length) return;

    const visible = (point) => point && point.visibility >= 0.45;
    this.poseCtx.lineCap = 'round';
    this.poseCtx.lineJoin = 'round';
    this.poseCtx.lineWidth = 4;
    this.poseCtx.strokeStyle = '#00e5ff';
    this.poseCtx.shadowColor = 'rgba(0, 0, 0, 0.75)';
    this.poseCtx.shadowBlur = 4;

    this.poseConnections.forEach(([fromName, toName]) => {
      const from = points[fromName];
      const to = points[toName];
      if (!visible(from) || !visible(to)) return;

      this.poseCtx.beginPath();
      this.poseCtx.moveTo(from.x * width, from.y * height);
      this.poseCtx.lineTo(to.x * width, to.y * height);
      this.poseCtx.stroke();
    });

    this.poseCtx.shadowBlur = 3;
    Object.values(points).forEach((point) => {
      if (!visible(point)) return;
      this.poseCtx.beginPath();
      this.poseCtx.arc(point.x * width, point.y * height, 5, 0, Math.PI * 2);
      this.poseCtx.fillStyle = '#fff36b';
      this.poseCtx.fill();
      this.poseCtx.lineWidth = 2;
      this.poseCtx.strokeStyle = '#222';
      this.poseCtx.stroke();
    });

    this.poseCtx.shadowBlur = 0;
  }

  updateFPS() {
    const elapsed = (Date.now() - this.startTime) / 1000;
    if (elapsed > 0) {
      const fps = (this.frameCount / elapsed).toFixed(1);
      const latency = this.lastProcessingMs ? ` · ${this.lastProcessingMs} ms` : '';
      this.fpsCounter.textContent = `FPS: ${fps}${latency}`;
    }
  }

  updateStatus(text, isConnected) {
    this.statusText.textContent = text;
    if (isConnected) {
      this.statusIndicator.classList.add('connected');
    } else {
      this.statusIndicator.classList.remove('connected');
    }
  }

  toggleSkeleton() {
    this.isSkeletonVisible = !this.isSkeletonVisible;
    if (this.toggleSkeletonBtn) {
      this.toggleSkeletonBtn.textContent = this.isSkeletonVisible
        ? 'Скрыть скелет'
        : 'Показать скелет';
    }
    if (!this.isSkeletonVisible) {
      this.clearPose();
    }
  }

  stop() {
    this.isRunning = false;

    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnecting = false;
    this.waitingForResult = false;

    this.video.srcObject = null;
    this.fpsCounter.textContent = '';
    this.currentMovementName.textContent = 'Не определено';
    this.currentMovementConfidence.textContent = '0.0%';
    this.clearPose();

    this.startBtn.disabled = false;
    this.stopBtn.disabled = true;
    this.updateStatus('Остановлено', false);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  // Инициализируем только если это страница search.html
  if (document.getElementById('realtimeButton')) {
    new RealtimeController();
  }
});
