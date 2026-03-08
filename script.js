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
    const API_BASE_URL = (window.location.protocol === 'file:' || window.location.port !== '8000' && window.location.hostname === 'localhost')
        ? 'http://127.0.0.1:8000'
        : '';

    const questionsList = [
        "1. 今、あなたが一番疲れていることは何ですか？",
        "2. 人間関係で、よく繰り返してしまう出来事はありますか？",
        "3. 仕事や活動の中で、何度も起きる問題はありますか？",
        "4. 強いストレスを感じたとき、どんな感情になりますか？",
        "5. これまでの人生で、印象に残っている出来事はありますか？",
        "6. もし理想の状態があるとしたら、どんな人生になっていますか？",
        "7. ストレスを感じたとき、どんな行動をとることが多いですか？",
        "8. 自分にはどんな思考の癖があると思いますか？",
        "9. 周囲の人から、どんな性格だと言われることが多いですか？",
        "10. 今の人生で、特に変えたいと感じていることは何ですか？"
    ];

    let lastGeneratedReport = ""; // To hold the report locally for email sending

    // === Initialization ===
    generateFormFields();
    loadFormData();

    // Path check for new flow
    const path = window.location.pathname;
    if (path === '/analysis-form') {
        switchScreen('input');
        window.scrollTo(0, 0);
    } else if (path === '/analysis-result') {
        startAnalysisProcess();
    }

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
        // Disabled for new format
        addAgeBtn.style.display = 'none';
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

        const data = getFormData(); // getFormData internally reads the DOM value which was populated by loadFormData
        const hasData = data.some(item => item.answer);

        if (!hasData) {
            alert('入力データが見つかりません。再度フォームから入力してください。');
            window.location.href = '/analysis-form';
            return;
        }

        try {
            const report = await callBackendAPI(data);
            lastGeneratedReport = report; // Store for email

            // Render the report using the new layout and parsed sections
            renderReport(report);

            switchScreen('report');
        } catch (error) {
            console.error(error);
            alert(`解析中にエラーが発生しました。\n${error.message}`);
            window.location.href = '/analysis-form'; // Back to input on error
        }
    }

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



    function saveFormData() {
        const data = getFormData();
        localStorage.setItem('yayoi_form_data', JSON.stringify(data));
    }

    function loadFormData() {
        const savedDataJson = localStorage.getItem('yayoi_form_data');
        if (savedDataJson) {
            try {
                const savedData = JSON.parse(savedDataJson);
                savedData.forEach((item, index) => {
                    const input = document.querySelector(`.question-input[data-index="${index}"]`);
                    // handle case where saved data is old format or new format
                    if (input && item.answer !== undefined) {
                        input.value = item.answer || '';
                    }
                });
            } catch (e) {
                console.error("Failed to parse saved data", e);
            }
        }
    }

    function getFormData() {
        const data = [];
        const savedDataJson = localStorage.getItem('yayoi_form_data');
        if (savedDataJson) {
            try {
                const savedData = JSON.parse(savedDataJson);
                return savedData;
            } catch (e) {
                console.error("Failed to parse saved data", e);
            }
        }

        const inputs = document.querySelectorAll('.question-input');
        inputs.forEach((input) => {
            const index = input.dataset.index;
            data.push({
                question: questionsList[index],
                answer: input.value.trim()
            });
        });
        return data;
    }


    async function callBackendAPI(historyData) {
        const formattedHistory = historyData
            .map(d => `【${d.question}】\n${d.answer || '（未回答）'}`)
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
