document.addEventListener('DOMContentLoaded', () => {
    // === DOM Elements ===
    const screens = {
        top: document.getElementById('top-screen'),
        input: document.getElementById('input-screen'),
        history: document.getElementById('history-screen'),
        loading: document.getElementById('loading-screen'),
        report: document.getElementById('report-screen'),
        'session-lp': document.getElementById('session-lp-screen')
    };

    const startBtn = document.getElementById('start-btn');
    const formContainer = document.getElementById('form-container');
    const historyContainer = document.getElementById('history-container');
    const saveLocalBtn = document.getElementById('save-local-btn');
    const analyzeBtn = document.getElementById('analyze-btn');
    const saveHistoryBtn = document.getElementById('save-history-btn');
    const startAnalysisBtn = document.getElementById('start-analysis-btn');
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
    const API_BASE_URL = (window.location.protocol === 'file:' || window.location.port !== '8000' && window.location.hostname === 'localhost')
        ? 'http://127.0.0.1:8000'
        : '';

    const questionsList = [
        "1 幼少期（0〜12歳）\nあなたの幼少期について教えてください。\n・家庭環境\n・親との関係\n・よく言われた言葉\n・その頃の自分の役割\n例\n長男としてしっかりしろと言われていた",
        "2 学生時代\n学校生活について教えてください。\n・友人関係\n・部活\n・リーダー経験\n・いじめや孤立の経験\nその時あなたはどんな感情でしたか？",
        "3 人生の大きな出来事\nこれまでの人生で印象的な出来事を教えてください。\n例\n・親の離婚\n・転校\n・挫折\n・成功体験\nその出来事で何を感じましたか？",
        "4 人間関係パターン\nあなたの人間関係には次のような傾向がありますか？\n・頼られやすい\n・我慢する\n・尽くしてしまう\n・距離を取る\n具体例を書いてください。",
        "5 仕事のパターン\n仕事ではどんな役割になりやすいですか？\n・リーダー\n・サポート\n・責任を背負う\n・期待される",
        "6 ストレス時の反応\nあなたはストレスを感じるとどんな行動を取りますか？\n例\n・一人になる\n・頑張りすぎる\n・逃げる\n・環境を変える",
        "7 今の悩み\n今一番悩んでいることを教えてください。",
        "8 変えたいこと\nこれから変えたいと思っている人生のテーマは何ですか？"
    ];

    let totalSteps = 9; // Default 1 to 9 (up to 45)

    const emotionsList = [
        "喜び", "安心", "誇り", "ワクワク", "愛情",
        "怒り", "悲しみ", "不安", "孤独", "無力感",
        "プレッシャー", "嫉妬", "焦り", "虚無感", "罪悪感"
    ];

    let lastGeneratedReport = ""; // To hold the report locally for email sending

    // === Initialization ===
    generateFormFields();
    generateHistoryFields(totalSteps);
    loadFormData();

    // === Routing Logic ===
    function handleRoute() {
        const path = window.location.pathname;
        const hash = window.location.hash;

        if (path === '/analysis-form') {
            switchScreen('input');
        } else if (path === '/analysis-result' || path === '/session-lp') {
            if (hash === '#session-lp' || path === '/session-lp') {
                switchScreen('session-lp');
            } else {
                // If on /analysis-result without hash, check for history data or show report
                // For now, default to history as per current flow
                switchScreen('history');
                loadHistoryData();
            }
        } else {
            // Default to top (LP)
            switchScreen('top');
        }
        window.scrollTo(0, 0);
    }

    // Initialize Routing
    handleRoute();

    // Listen for hash changes (e.g. from script or user back button)
    window.addEventListener('hashchange', handleRoute);

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
                    let errMessage = '送信エラーが発生しました。';
                    try {
                        const errObj = await response.json();
                        if (errObj.detail) errMessage = errObj.detail;
                    } catch (e) { }
                    throw new Error(errMessage);
                }

                alert(`${email} 宛にレポートを送信しました！\n数分経っても届かない場合は迷惑メールフォルダをご確認ください。\n（※無料システムのため、うまく送信できない環境もございます）`);
                emailModal.style.display = 'none';
            } catch (err) {
                alert(`メール送信エラー: ${err.message}\nお使いのメールサーバーで制限がかかっているか、内部設定の問題です。大変お手数ですが画面のPDF保存をご利用ください。`);
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

    const saveLocalBtnHighlight = document.getElementById('save-local-btn-highlight');
    if (saveLocalBtnHighlight) {
        saveLocalBtnHighlight.addEventListener('click', () => {
            saveFormData();
            alert('入力データをブラウザに保存しました。\n大変お手数ですが、このまま下へ進み「人生構造レポートを生成する」ボタンにお進みください。');
        });
    }

    if (addAgeBtn) {
        addAgeBtn.addEventListener('click', () => {
            totalSteps++;
            const newBlock = createStepBlockElement(totalSteps);
            historyContainer.appendChild(newBlock);
            saveHistoryData();
        });
    }

    if (saveHistoryBtn) {
        saveHistoryBtn.addEventListener('click', () => {
            saveHistoryData();
            alert('自分史データを一時保存しました。');
        });
    }

    if (startAnalysisBtn) {
        startAnalysisBtn.addEventListener('click', () => {
            saveHistoryData(); // Auto-save
            startAnalysisProcess();
        });
    }

    analyzeBtn.addEventListener('click', async () => {
        saveFormData(); // Auto-save on start
        const data = getFormData();

        const hasData = data.some(item => item.answer);
        if (!hasData) {
            if (!confirm('入力データが空ですが、このまま決済に進みますか？')) {
                return;
            }
        }

        // 入力完了後、Stripe決済画面へリダイレクト
        window.location.href = 'https://buy.stripe.com/bJe8wIfTm42CbIf2Vn9k401';
    });

    async function startAnalysisProcess() {
        switchScreen('loading');
        window.scrollTo(0, 0);

        const formData = getFormData();
        const historyData = getHistoryData();

        const hasFormData = formData.some(item => item.answer);
        const hasHistoryData = historyData.length > 0 && historyData.some(d => d.events || d.emotions.length > 0 || d.emotionsOther || d.actions || d.people);

        if (!hasHistoryData) {
            renderReport('分析に必要な人生情報が不足しています。\n自分史の入力内容を見直して、もう一度入力してください。');
            switchScreen('report');
            return;
        }

        if (!hasFormData) {
            alert('8つの質問のデータが見つかりません。\nお手数ですが最初の質問フォームからやり直してください。');
            window.location.href = '/analysis-form';
            return;
        }

        try {
            const report = await callBackendAPI(formData, historyData);
            lastGeneratedReport = report;
            renderReport(report);
            switchScreen('report');
        } catch (error) {
            console.error(error);
            alert(`解析中にエラーが発生しました。\n${error.message}`);
            window.location.href = '/analysis-form';
        }
    }

    if (printBtn) {
        printBtn.addEventListener('click', () => {
            window.print();
        });
    }

    if (clearDataBtn) {
        clearDataBtn.addEventListener('click', () => {
            if (confirm('ブラウザに保存されている詳細な人生データを完全に消去します。よろしいですか？')) {
                localStorage.removeItem('yayoi_form_data');
                localStorage.removeItem('yayoi_history_data');
                alert('データを消去しました。トップ画面に戻ります。');
                location.reload();
            }
        });
    }

    // === Helper Functions ===
    function switchScreen(targetScreenName) {
        Object.values(screens).forEach(screen => {
            screen.classList.remove('active');
        });
        screens[targetScreenName].classList.add('active');
    }

    function generateFormFields() {
        formContainer.innerHTML = '';
        const stepBlock = document.createElement('div');
        stepBlock.className = 'step-block';

        let html = '';
        questionsList.forEach((q, index) => {
            html += `
                <div class="form-group" style="margin-bottom: 2rem;">
                    <label style="font-size: 1.1rem; font-weight: bold; color: #333; display: block; margin-bottom: 0.5rem;">${q}</label>
                    <textarea class="question-input" data-index="${index}" placeholder="回答を入力してください" style="width: 100%; min-height: 100px; padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 1rem; font-family: inherit; resize: vertical;"></textarea>
                </div>
            `;
        });

        stepBlock.innerHTML = html;
        formContainer.appendChild(stepBlock);
    }

    // === History Form Functions ===
    function generateHistoryFields(stepsCount) {
        if (!historyContainer) return;
        historyContainer.innerHTML = '';
        for (let step = 1; step <= stepsCount; step++) {
            historyContainer.appendChild(createStepBlockElement(step));
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
                    <textarea class="event-input" placeholder="例：小学校入学、引越し、親の離婚など"></textarea>
                </div>

                <div class="form-group">
                    <label>当時の感情</label>
                    <span class="hint">その出来事に対して、どう感じていましたか？（複数選択可）</span>
                    <div class="checkbox-group">
                        ${emotionCheckboxes}
                    </div>
                    <input type="text" class="emotion-other-input" placeholder="その他の感情・自由入力">
                </div>

                <div class="form-group">
                    <label>自分が取った行動・選択</label>
                    <span class="hint">その出来事や感情に対して、自分はどう動きましたか？</span>
                    <textarea class="action-input" placeholder="例：親の期待に応えるために勉強ばかりした、反発したなど"></textarea>
                </div>

                <div class="form-group">
                    <label>周囲の主要人物</label>
                    <span class="hint">この時期、あなたに最も影響を与えた人物は誰ですか？</span>
                    <input type="text" class="people-input" placeholder="例：母親、厳しい部活の先生、親友など">
                </div>
            </div>
        `;
        return stepBlock;
    }

    function saveHistoryData() {
        const data = getHistoryData();
        localStorage.setItem('yayoi_history_data', JSON.stringify(data));
    }

    function loadHistoryData() {
        const savedDataJson = localStorage.getItem('yayoi_history_data');
        if (savedDataJson) {
            try {
                const savedData = JSON.parse(savedDataJson);
                if (savedData.length > totalSteps) {
                    totalSteps = savedData.length;
                    generateHistoryFields(totalSteps);
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
                console.error("Failed to parse saved history data", e);
            }
        }
    }

    function getHistoryData() {
        const data = [];
        for (let step = 1; step <= totalSteps; step++) {
            const block = document.querySelector(`.step-block[data-step="${step}"]`);
            if (!block) continue;

            const ageBlock = block.querySelector('.age-block');
            if (!ageBlock) continue;

            const rangeLabel = ageBlock.dataset.range;
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

    function saveFormData() {
        const data = getFormData();
        localStorage.setItem('yayoi_form_data', JSON.stringify(data));
    }

    function loadFormData() {
        const savedDataJson = localStorage.getItem('yayoi_form_data');
        if (savedDataJson) {
            try {
                const savedData = JSON.parse(savedDataJson);
                // 既存の保存データにテキストがある場合は順番に詰め込む（質問内容が変わっていても回答のテキストを復元）
                let indexToRestore = 0;
                savedData.forEach((item) => {
                    if (item.answer && item.answer.trim() !== '') {
                        const input = document.querySelector(`.question-input[data-index="${indexToRestore}"]`);
                        if (input) {
                            input.value = item.answer || '';
                            indexToRestore++;
                        }
                    }
                });
            } catch (e) {
                console.error("Failed to parse saved data", e);
            }
        }
    }

    function getFormData() {
        const data = [];
        const inputs = document.querySelectorAll('.question-input');

        // If inputs exist on the screen, use their current values (this handles the first screen case)
        if (inputs.length > 0) {
            inputs.forEach((input) => {
                const index = input.dataset.index;
                data.push({
                    question: questionsList[index],
                    answer: input.value.trim()
                });
            });
            return data;
        }

        const savedDataJson = localStorage.getItem('yayoi_form_data');
        if (savedDataJson) {
            try {
                const savedData = JSON.parse(savedDataJson);
                return savedData;
            } catch (e) {
                console.error("Failed to parse saved data", e);
            }
        }

        return data;
    }


    async function callBackendAPI(formData, historyData) {
        // 8つの質問の答えをAPIのプロンプト引数にマッピング
        const childhood = formData[0]?.answer || "未回答";
        const student = formData[1]?.answer || "未回答";

        // 質問3（人生の出来事）＋自分史（5年ごと）を統合
        let events = formData[2]?.answer || "未回答";
        const historyText = historyData
            .filter(d => d.events || d.emotions.length > 0 || d.emotionsOther || d.actions || d.people)
            .map(d => {
                let emoText = d.emotions.join('、');
                if (d.emotionsOther) emoText += emoText ? `、${d.emotionsOther}` : d.emotionsOther;
                return `【${d.range}】\n・出来事: ${d.events}\n・感情: ${emoText}\n・行動: ${d.actions}\n・主要人物: ${d.people}`;
            })
            .join('\n\n');
        if (historyText) {
            events += "\n\n【自分史（5年ごと）】\n" + historyText;
        }

        const relationships = formData[3]?.answer || "未回答";
        const work = formData[4]?.answer || "未回答";
        const stress = formData[5]?.answer || "未回答";
        const problem = formData[6]?.answer || "未回答";
        const change = formData[7]?.answer || "未回答";

        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                childhood: childhood,
                student: student,
                events: events,
                relationships: relationships,
                work: work,
                stress: stress,
                problem: problem,
                change: change
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
        if (markdownText.includes("分析に必要な人生情報が不足しています") || markdownText.includes("分析に必要な情報が不足しています")) {
            reportContent.innerHTML = `
                <div class="report-header-nav no-print" style="margin-bottom: 2rem;">
                    <button class="nav-link-btn" id="nav-top">◀ 自分史入力に戻る</button>
                </div>
                <div class="report-section" style="text-align: center;">
                    <h3 style="color: #d9534f; border:none; padding:0;">分析情報が不足しています</h3>
                    <p style="margin: 20px 0; font-weight: bold; line-height: 1.6; color: #333;">
                        ${markdownText.replace(/\n/g, '<br>')}
                    </p>
                    <button id="nav-history-btn" class="primary-btn" style="max-width: 300px; width: 100%;">自分史入力画面に戻る</button>
                </div>
            `;
            document.getElementById('nav-top').addEventListener('click', () => { switchScreen('history'); window.scrollTo(0, 0); });
            document.getElementById('nav-history-btn').addEventListener('click', () => { switchScreen('history'); window.scrollTo(0, 0); });
            return;
        }

        // 10のセクションに分割
        const sections = {};
        const sectionRegex = /## (\d+)\s+(.*?)\n([\s\S]*?)(?=(## \d+|$))/g;
        let match;
        while ((match = sectionRegex.exec(markdownText)) !== null) {
            sections[match[1]] = { title: match[2].trim(), content: match[3].trim() };
        }

        // ヘルパー: コンテンツの整形（改行、強調）
        const format = (text) => text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');

        // 各セクションのHTML構築
        let html = `
            <div class="report-header-nav no-print">
                <button class="nav-link-btn" id="nav-top">◀ 自分史入力に戻る</button>
                <button class="nav-link-btn" id="nav-input">◀ 質問フォームに戻る</button>
            </div>
            <div class="report-title-section">
                <p style="color: var(--primary-color); font-weight: 700; margin-bottom: 1rem;">Personal Analysis Report</p>
                <h1>人生構造分析レポート</h1>
                <p class="report-subtitle">あなたの人生に繰り返されている「行動・感情・環境」のパターンを分析しました</p>
            </div>
        `;

        // 1. 人生の流れ
        if (sections["1"]) {
            html += `
                <div class="report-section">
                    <div class="report-section-header">LIFE FLOW</div>
                    <h2 class="report-main-h">${sections["1"].title}</h2>
                    <p class="report-text" style="font-size: 1.1rem; line-height: 2;">${format(sections["1"].content)}</p>
                </div>
            `;
        }

        // 2. 転換点
        if (sections["2"]) {
            const tpBlocks = sections["2"].content.split(/\n\d+\.\s/).filter(b => b.trim());
            let tpCards = tpBlocks.map(block => {
                const lines = block.trim().split(/\n/);
                const event = lines[0] || "重要な出来事";
                const details = lines.slice(1).join('<br>');
                return `
                    <div class="turning-point-card">
                        <div class="tp-event">${event}</div>
                        <div class="tp-meaning">${format(details)}</div>
                    </div>
                `;
            }).join('');

            html += `
                <div class="report-section">
                    <div class="report-section-header">TURNING POINTS</div>
                    <h2 class="report-main-h">${sections["2"].title}</h2>
                    <div class="turning-point-container">${tpCards}</div>
                </div>
            `;
        }

        // 3. 構造図
        if (sections["3"]) {
            const nodes = sections["3"].content.split(/↓/).map(n => n.trim().replace(/^[・\-\s]*/, ""));
            const diagramHtml = nodes.map((node, i) => `
                <div class="structure-node">${node}</div>
                ${i < nodes.length - 1 ? '<div class="structure-arrow">↓</div>' : '<div class="structure-arrow">↓</div><div class="structure-node" style="opacity:0.5; font-size:0.8rem;">（最初に戻る）</div>'}
            `).join('');

            html += `
                <div class="report-section">
                    <div class="report-section-header">STRUCTURE LOOP</div>
                    <h2 class="report-main-h">${sections["3"].title}</h2>
                    <div class="structure-diagram">${diagramHtml}</div>
                </div>
            `;
        }

        // 4. 無意識ルール
        if (sections["4"]) {
            html += `
                <div class="report-section">
                    <div class="report-section-header">UNCONSCIOUS RULE</div>
                    <h2 class="report-main-h">${sections["4"].title}</h2>
                    <div class="highlight-box">
                        <p class="report-text" style="font-size: 1.25rem; text-align: center; font-weight: bold; color: #b45309; line-height: 1.6;">
                            ${format(sections["4"].content)}
                        </p>
                    </div>
                </div>
            `;
        }

        // 5 & 6. 強みと代償
        if (sections["5"] || sections["6"]) {
            html += `
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-bottom: 2.5rem;">
                    <div class="report-section" style="margin-bottom: 0;">
                        <div class="report-section-header">STRENGTH</div>
                        <h4 class="report-h4">${sections["5"]?.title || "この構造の強み"}</h4>
                        <p class="report-text">${format(sections["5"]?.content || "")}</p>
                    </div>
                    <div class="report-section" style="margin-bottom: 0; background: #fffcfc; border-color: #fee;">
                        <div class="report-section-header" style="color: #e53e3e;">COST</div>
                        <h4 class="report-h4" style="color: #c53030;">${sections["6"]?.title || "この構造の代償"}</h4>
                        <p class="report-text">${format(sections["6"]?.content || "")}</p>
                    </div>
                </div>
            `;
        }

        // 7. 未来
        if (sections["7"]) {
            html += `
                <div class="report-section">
                    <div class="report-section-header">FUTURE</div>
                    <h2 class="report-main-h">${sections["7"].title}</h2>
                    <div class="danger-box">
                        <p class="report-text">${format(sections["7"].content)}</p>
                    </div>
                </div>
            `;
        }

        // 8. タイプ
        if (sections["8"]) {
            const typeName = sections["8"].content.split(/\n/)[0].replace(/[「（）]/g, '').trim();
            html += `
                <div class="report-section" style="text-align: center; border: 2px solid var(--primary-color);">
                    <div class="report-section-header" style="justify-content: center;">TYPE</div>
                    <h2 class="report-main-h">${sections["8"].title}</h2>
                    <div class="type-badge">${typeName}</div>
                    <p class="report-text" style="text-align: left; margin-top: 1.5rem;">${format(sections["8"].content.replace(typeName, "").trim())}</p>
                </div>
            `;
        }

        // 9. ヒント
        if (sections["9"]) {
            html += `
                <div class="report-section">
                    <div class="report-section-header">HINTS</div>
                    <h2 class="report-main-h">${sections["9"].title}</h2>
                    <p class="report-text">${format(sections["9"].content)}</p>
                </div>
            `;
        }

        // 10. 最後 & 下部ボタン
        if (sections["10"]) {
            html += `
                <div class="next-step-section">
                    <div class="report-section-header" style="color: #888; border-color: #444; justify-content: center;">MESSAGE</div>
                    <p>${format(sections["10"].content.replace("▶ 構造解析セッションを見る", ""))}</p>
                    <button id="nav-session-lp-btn" class="btn-premium">▶ 構造解析セッションを見る</button>
                </div>

                <div class="report-section no-print" style="margin-top: 4rem; text-align: center; border: 1px dashed #ccc;">
                    <h3 style="border:none; padding:0; margin-bottom: 1.5rem;">このレポートを保存する</h3>
                    <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
                        <button id="open-email-modal-btn" class="primary-btn" style="max-width: 250px; font-size: 0.9rem;">✉️ メールで受け取る</button>
                        <button id="save-pdf-btn-report" class="secondary-btn" style="max-width: 250px; padding: 0.8rem; font-size: 0.9rem;">PDFで保存 / 印刷</button>
                    </div>
                    <p style="font-size: 0.8rem; color: #888; margin-top: 1.5rem;">
                        ※データ保護のため、ブラウザを閉じると消去される場合があります。<br>大切な解析結果は必ず保存してください。
                    </p>
                    <button id="clear-data-btn-report" class="danger-btn" style="margin-top: 2rem; padding: 0.5rem 1rem; font-size: 0.8rem; opacity: 0.6;">全ての入力データを消去して終了</button>
                </div>
            `;
        }

        reportContent.innerHTML = html;

        // イベントリスナーの再設定
        document.getElementById('nav-top')?.addEventListener('click', () => { switchScreen('history'); window.scrollTo(0, 0); });
        document.getElementById('nav-input')?.addEventListener('click', () => { switchScreen('input'); window.scrollTo(0, 0); });
        document.getElementById('nav-session-lp-btn')?.addEventListener('click', () => { window.location.hash = 'session-lp'; });
        document.getElementById('save-pdf-btn-report')?.addEventListener('click', () => window.print());
        document.getElementById('open-email-modal-btn')?.addEventListener('click', () => { emailModal.style.display = 'flex'; });
        document.getElementById('clear-data-btn-report')?.addEventListener('click', () => {
            if (confirm('ブラウザに保存されている詳細な人生データを完全に消去します。よろしいですか？')) {
                localStorage.removeItem('yayoi_form_data');
                localStorage.removeItem('yayoi_history_data');
                alert('データを消去しました。トップ画面に戻ります。');
                location.href = '/';
            }
        });
    }

    // 外部から呼べるようにする
    window.switchScreen = switchScreen;
});
