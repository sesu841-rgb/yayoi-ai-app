document.addEventListener('DOMContentLoaded', () => {
    // === DOM Elements ===
    const screens = {
        top: document.getElementById('top-screen'),
        input: document.getElementById('input-screen'),
        loading: document.getElementById('loading-screen'),
        report: document.getElementById('report-screen')
    };

    const startBtn = document.getElementById('start-btn');
    const formContainer = document.getElementById('form-container');
    const saveLocalBtn = document.getElementById('save-local-btn');
    const analyzeBtn = document.getElementById('analyze-btn');
    const addAgeBtn = document.getElementById('add-age-btn');
    const printBtn = document.getElementById('print-btn');
    const clearDataBtn = document.getElementById('clear-data-btn');
    const reportContent = document.getElementById('report-content');

    const emailModal = document.getElementById('email-modal');
    const modalCloseBtn = document.getElementById('modal-close-btn');
    const modalCancelBtn = document.getElementById('modal-cancel-btn');
    const sendEmailBtn = document.getElementById('send-email-btn');
    const emailInput = document.getElementById('email-input');

    // === Constants & State ===
    let totalSteps = 9; // Default 1 to 9 (up to 45)

    const emotionsList = [
        "喜び", "安心", "誇り", "ワクワク", "愛情",
        "怒り", "悲しみ", "不安", "孤独", "無力感",
        "プレッシャー", "嫉妬", "焦り", "虚無感", "罪悪感"
    ];

    let lastGeneratedReport = ""; // To hold the report locally for email sending

    // === Initialization ===
    generateFormFields(totalSteps);
    loadFormData();

    // === Event Listeners ===
    startBtn.addEventListener('click', () => {
        switchScreen('input');
        window.scrollTo(0, 0);
    });

    [modalCloseBtn, modalCancelBtn].forEach(btn => {
        if (btn) {
            btn.addEventListener('click', () => {
                emailModal.style.display = 'none';
            });
        }
    });

    if (sendEmailBtn) {
        sendEmailBtn.addEventListener('click', async () => {
            const email = emailInput.value.trim();
            if (!email) {
                alert('メールアドレスを入力してください。');
                return;
            }
            if (!lastGeneratedReport) {
                alert('レポートが生成されていません。');
                return;
            }

            try {
                // Change button text and disable it to show loading state
                const originalText = sendEmailBtn.textContent;
                sendEmailBtn.textContent = '送信中...';
                sendEmailBtn.disabled = true;

                const response = await fetch(`${API_BASE_URL || ''}/send-report`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        email: email,
                        report_markdown: lastGeneratedReport
                    })
                });

                if (!response.ok) {
                    throw new Error('送信エラーが発生しました。');
                }

                alert(`${email} 宛にレポート送信リクエストを完了しました！\n（※SMTP設定がない場合はコンソール上のシミュレーションになります）`);
                emailModal.style.display = 'none';
            } catch (err) {
                alert(err.message);
            } finally {
                sendEmailBtn.textContent = '送信する';
                sendEmailBtn.disabled = false;
            }
        });
    }

    saveLocalBtn.addEventListener('click', () => {
        saveFormData();
        alert('入力データをブラウザに保存しました。');
    });

    if (addAgeBtn) {
        addAgeBtn.addEventListener('click', () => {
            saveFormData();
            totalSteps++;
            formContainer.appendChild(createStepBlockElement(totalSteps));
        });
    }

    analyzeBtn.addEventListener('click', async () => {
        saveFormData(); // Auto-save on start
        const data = getFormData();

        const hasData = data.some(item => item.events || item.emotions.length > 0 || item.actions || item.people);
        if (!hasData) {
            if (!confirm('入力データが空ですが、このまま解析を実行しますか？')) {
                return;
            }
        }

        switchScreen('loading');

        try {
            const report = await callBackendAPI(data);
            lastGeneratedReport = report; // Store for email

            // Render the report using the new layout and parsed sections
            renderReport(report);

            switchScreen('report');
        } catch (error) {
            console.error(error);
            alert(`解析中にエラーが発生しました。\n${error.message}`);
            switchScreen('input'); // Back to input on error
        }
    });

    printBtn.addEventListener('click', () => {
        window.print();
    });

    clearDataBtn.addEventListener('click', () => {
        if (confirm('ブラウザに保存されている詳細な人生データを完全に消去します。よろしいですか？')) {
            localStorage.removeItem('yayoi_form_data');
            alert('データを消去しました。トップ画面に戻ります。');
            location.reload();
        }
    });

    // === Helper Functions ===
    function switchScreen(targetScreenName) {
        Object.values(screens).forEach(screen => {
            screen.classList.remove('active');
        });
        screens[targetScreenName].classList.add('active');
    }

    function generateFormFields(stepsCount) {
        formContainer.innerHTML = '';
        for (let step = 1; step <= stepsCount; step++) {
            formContainer.appendChild(createStepBlockElement(step));
        }
    }

    function createStepBlockElement(step) {
        let startAge = 0;
        let endAge = 5;
        let label = "基本情報（年齢確認）等";

        if (step === 1) {
            startAge = 0;
            endAge = 5;
            label = `0～5歳`;
        } else {
            startAge = (step - 1) * 5 + 1;
            endAge = step * 5;
            label = `${startAge}～${endAge}歳`;
        }

        const stepBlock = document.createElement('div');
        stepBlock.className = 'step-block';
        stepBlock.dataset.step = step;

        const emotionCheckboxes = emotionsList.map((emo) => `
            <label class="checkbox-label">
                <input type="checkbox" name="emotion_${step}" value="${emo}">
                <span>${emo}</span>
            </label>
        `).join('');

        stepBlock.innerHTML = `
            <div class="age-block" data-range="${label}">
                <div class="age-label">${label}</div>
                
                <div class="form-group">
                    <label>印象的な出来事</label>
                    <span class="hint">この時期に起きた一番大きな出来事や環境の変化を事実ベースで書いてください。</span>
                    <textarea class="event-input" placeholder="例: 小学校入学、引越し、親の離婚など"></textarea>
                </div>

                <div class="form-group">
                    <label>当時の感情</label>
                    <span class="hint">その出来事に対して、どう感じていましたか？（複数選択可）</span>
                    <div class="checkbox-group">
                        ${emotionCheckboxes}
                    </div>
                    <input type="text" class="emotion-other-input" placeholder="その他の感情（自由入力）">
                </div>

                <div class="form-group">
                    <label>自分が取った行動（選択）</label>
                    <span class="hint">その出来事や感情に対して、自分はどう行動しましたか？</span>
                    <textarea class="action-input" placeholder="例: 親の期待に応えるために勉強ばかりした、反発したなど"></textarea>
                </div>

                <div class="form-group">
                    <label>周囲の主要人物</label>
                    <span class="hint">この時期、あなたに最も影響を与えた人物は誰ですか？</span>
                    <input type="text" class="people-input" placeholder="例: 母親、厳しい担任の先生、親友など">
                </div>
            </div>
        `;
        return stepBlock;
    }



    function saveFormData() {
        const data = getFormData();
        localStorage.setItem('yayoi_form_data', JSON.stringify(data));
    }

    function loadFormData() {
        const savedDataJson = localStorage.getItem('yayoi_form_data');
        if (savedDataJson) {
            try {
                const savedData = JSON.parse(savedDataJson);
                if (savedData.length > totalSteps) {
                    totalSteps = savedData.length;
                    generateFormFields(totalSteps);
                }
                savedData.forEach((item, index) => {
                    const step = index + 1;
                    const block = document.querySelector(`.step-block[data-step="${step}"]`);
                    if (!block) return;

                    const eventInput = block.querySelector('.event-input');
                    const actionInput = block.querySelector('.action-input');
                    const peopleInput = block.querySelector('.people-input');
                    const emotionOtherInput = block.querySelector('.emotion-other-input');

                    if (eventInput) eventInput.value = item.events || '';
                    if (actionInput) actionInput.value = item.actions || '';
                    if (peopleInput) peopleInput.value = item.people || '';
                    if (emotionOtherInput) emotionOtherInput.value = item.emotionsOther || '';

                    const checkboxes = block.querySelectorAll(`input[name="emotion_${step}"]`);
                    checkboxes.forEach(cb => {
                        cb.checked = (item.emotions && item.emotions.includes(cb.value));
                    });
                });
            } catch (e) {
                console.error("Failed to parse saved data", e);
            }
        }
    }

    function getFormData() {
        const data = [];
        for (let step = 1; step <= totalSteps; step++) {
            const block = document.querySelector(`.step-block[data-step="${step}"]`);
            if (!block) continue;

            const rangeLabel = block.querySelector('.age-block').dataset.range;
            const eventVal = block.querySelector('.event-input').value.trim();
            const actionVal = block.querySelector('.action-input').value.trim();
            const peopleVal = block.querySelector('.people-input').value.trim();
            const emotionOtherVal = block.querySelector('.emotion-other-input').value.trim();

            const emotionsSelected = Array.from(block.querySelectorAll(`input[name="emotion_${step}"]:checked`)).map(cb => cb.value);

            data.push({
                range: rangeLabel,
                events: eventVal,
                emotions: emotionsSelected,
                emotionsOther: emotionOtherVal,
                actions: actionVal,
                people: peopleVal
            });
        }
        return data;
    }

    const API_BASE_URL = (window.location.protocol === 'file:' || window.location.port !== '8000' && window.location.hostname === 'localhost')
        ? 'http://127.0.0.1:8000'
        : '';

    async function callBackendAPI(historyData) {
        const formattedHistory = historyData
            .filter(d => d.events || d.emotions.length > 0 || d.emotionsOther || d.actions || d.people)
            .map(d => {
                let emoText = d.emotions.join('、');
                if (d.emotionsOther) {
                    emoText += emoText ? `、${d.emotionsOther}` : d.emotionsOther;
                }
                return `【${d.range}】\n・印象的な出来事: ${d.events}\n・当時の感情: ${emoText}\n・取った行動: ${d.actions}\n・周囲の主要人物: ${d.people}`;
            })
            .join('\n\n');

        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                formattedHistory: formattedHistory
            })
        });

        if (!response.ok) {
            let errorMsg = 'APIリクエストに失敗しました。';
            try {
                const err = await response.json();
                errorMsg = err.detail || errorMsg;
            } catch (e) { }
            throw new Error(errorMsg);
        }

        const result = await response.json();
        return result.report;
    }

    function renderReport(markdownText) {
        // Very simple logic to format markdown into the custom blocks
        let html = markdownText
            .replace(/### (.*?)\n/g, '<h4 class="report-h4">$1</h4>')
            .replace(/## (.*?)\n/g, '<h3 class="report-section-title">$1</h3>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n\n/g, '</p><p class="report-text">')
            .replace(/\n/g, '<br>');

        html = `<p class="report-text">${html}</p>`;

        // Add the CTA buttons and structural blocks requested
        reportContent.innerHTML = `
            <div class="report-header-nav no-print">
                <button class="nav-link-btn" id="nav-top">◀ トップに戻る</button>
                <button class="nav-link-btn" id="nav-input">◀ 入力画面に戻る</button>
            </div>
            
            <div class="report-intro">
                ${html}
            </div>

            <div class="report-save-section no-print">
                <h3>このままでも生きられます。<br>ただ、同じ場面はまた来ます。</h3>
                <p>構造が見えただけでは、現実は変わりません。<br>書き換えには、理解ではなく実行が必要です。</p>
                
                <h4 style="margin-top: 2rem; margin-bottom: 1rem; color: #333;">このレポートを保存しますか？</h4>
                <div class="save-buttons">
                    <button id="open-email-modal-btn" class="primary-btn" style="width: 100%;">✉️ メールで受け取る</button>
                    <button id="save-pdf-btn" class="secondary-btn" style="width: 100%; margin-top: 10px;">PDFとして保存する</button>
                </div>
                <p style="text-align: center; font-size: 0.85rem; color: #666; margin-top: 10px;">
                    ※印刷画面が開きます。<br>送信先（プリンター）を「PDFに保存」に変更してください。
                </p>
            </div>

            <div class="report-cta-block no-print">
                <h3>この構造を書き換える</h3>
                <p>構造個別セッションでは、<br>あなたの反応を一つに絞り、<br>止め方まで決めます。</p>
                
                <div class="cta-buttons">
                    <a href="#" class="primary-btn cta-btn">▶ 構造個別セッション（入口）</a>
                </div>
                <p style="font-size: 0.85rem; margin-top: 25px; text-align: center; color: #555; line-height: 1.6;">※90日伴走プログラムは、<br>個別セッション後にご案内します。</p>
            </div>
        `;

        // Attach event listeners to the new nav buttons
        document.getElementById('nav-top').addEventListener('click', () => {
            switchScreen('top');
            window.scrollTo(0, 0);
        });

        document.getElementById('nav-input').addEventListener('click', () => {
            switchScreen('input');
            window.scrollTo(0, 0);
        });

        document.getElementById('save-pdf-btn').addEventListener('click', () => {
            window.print();
        });

        document.getElementById('open-email-modal-btn').addEventListener('click', () => {
            if (emailModal) {
                emailModal.style.display = 'flex';
            } else {
                document.getElementById('email-modal').style.display = 'flex';
            }
        });
    }
});
