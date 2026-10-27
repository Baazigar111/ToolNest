/**
 * ToolNest Client-Side Interactive Tools
 * High performance, zero-dependency vanilla JavaScript for browser tools.
 * Handles: Word Counter, Case Converter, JSON Formatter, EMI, SIP, and GST Calculators.
 */

// Currency formatting helper (Indian numbering system: ₹ 1,00,000)
function formatCurrency(num, decimals = 0) {
  if (isNaN(num) || !isFinite(num)) return '₹ 0';
  const fixed = Number(num).toFixed(decimals);
  const parts = fixed.split('.');
  let integerPart = parts[0];
  const decimalPart = parts.length > 1 ? '.' + parts[1] : '';

  const lastThree = integerPart.substring(integerPart.length - 3);
  const otherNumbers = integerPart.substring(0, integerPart.length - 3);
  const formatted = otherNumbers !== ''
    ? otherNumbers.replace(/\B(?=(\d{2})+(?!\d))/g, ',') + ',' + lastThree
    : lastThree;

  return '₹ ' + formatted + decimalPart;
}

// -------------------------------------------------------------
// 1. Word Counter
// -------------------------------------------------------------
function initWordCounter() {
  const input = document.getElementById('word-input');
  if (!input) return;

  const statWords = document.getElementById('stat-words');
  const statChars = document.getElementById('stat-chars');
  const statCharsNoSpace = document.getElementById('stat-chars-no-spaces');
  const statSentences = document.getElementById('stat-sentences');
  const statParagraphs = document.getElementById('stat-paragraphs');
  const statReadingTime = document.getElementById('stat-reading-time');
  const statSpeakingTime = document.getElementById('stat-speaking-time');
  const btnClear = document.getElementById('btn-clear-words');

  function calculateStats() {
    const text = input.value || '';
    const trimmed = text.trim();

    // Characters
    const chars = text.length;
    const charsNoSpace = text.replace(/\s/g, '').length;

    // Words
    const words = trimmed ? trimmed.split(/\s+/).filter(Boolean).length : 0;

    // Sentences
    const sentences = trimmed
      ? (trimmed.match(/[^.!?]+[.!?]+(\s|$)/g) || []).length || 1
      : 0;

    // Paragraphs
    const paragraphs = trimmed
      ? text.split(/\n+/).filter(p => p.trim().length > 0).length
      : 0;

    // Reading & Speaking times
    const readMinutes = Math.ceil(words / 200);
    const speakMinutes = Math.ceil(words / 130);

    if (statWords) statWords.textContent = words.toLocaleString();
    if (statChars) statChars.textContent = chars.toLocaleString();
    if (statCharsNoSpace) statCharsNoSpace.textContent = charsNoSpace.toLocaleString();
    if (statSentences) statSentences.textContent = sentences.toLocaleString();
    if (statParagraphs) statParagraphs.textContent = paragraphs.toLocaleString();
    if (statReadingTime) statReadingTime.textContent = words < 60 && words > 0 ? '< 1m' : `${readMinutes}m`;
    if (statSpeakingTime) statSpeakingTime.textContent = words < 40 && words > 0 ? '< 1m' : `${speakMinutes}m`;
  }

  input.addEventListener('input', calculateStats);
  input.addEventListener('paste', () => setTimeout(calculateStats, 50));

  if (btnClear) {
    btnClear.addEventListener('click', () => {
      input.value = '';
      calculateStats();
      input.focus();
    });
  }

  calculateStats();
}

// -------------------------------------------------------------
// 2. Case Converter
// -------------------------------------------------------------
function initCaseConverter() {
  const input = document.getElementById('case-input');
  if (!input) return;

  const charCountEl = document.getElementById('case-char-count');
  const wordCountEl = document.getElementById('case-word-count');
  const btnClear = document.getElementById('btn-clear-case');

  function updateCounts() {
    const text = input.value || '';
    if (charCountEl) charCountEl.textContent = text.length.toLocaleString();
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    if (wordCountEl) wordCountEl.textContent = words.toLocaleString();
  }

  input.addEventListener('input', updateCounts);
  updateCounts();

  function getWords(text) {
    return text.trim().split(/[\s_\-]+/).filter(Boolean);
  }

  const actions = {
    'btn-uppercase': text => text.toUpperCase(),
    'btn-lowercase': text => text.toLowerCase(),
    'btn-titlecase': text =>
      text.toLowerCase().replace(/\b\w/g, char => char.toUpperCase()),
    'btn-sentencecase': text =>
      text.toLowerCase().replace(/(^\s*\w|[.!?]\s*\w)/g, c => c.toUpperCase()),
    'btn-camelcase': text => {
      const words = getWords(text);
      if (words.length === 0) return '';
      return words
        .map((w, i) => (i === 0 ? w.toLowerCase() : w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()))
        .join('');
    },
    'btn-snakecase': text => getWords(text).map(w => w.toLowerCase()).join('_'),
    'btn-kebabcase': text => getWords(text).map(w => w.toLowerCase()).join('-'),
  };

  Object.entries(actions).forEach(([id, transform]) => {
    const btn = document.getElementById(id);
    if (btn) {
      btn.addEventListener('click', () => {
        if (!input.value) return;
        input.value = transform(input.value);
        updateCounts();
      });
    }
  });

  if (btnClear) {
    btnClear.addEventListener('click', () => {
      input.value = '';
      updateCounts();
      input.focus();
    });
  }
}

// -------------------------------------------------------------
// 3. JSON Formatter & Validator
// -------------------------------------------------------------
function initJsonFormatter() {
  const input = document.getElementById('json-input');
  if (!input) return;

  const statusBanner = document.getElementById('json-status-banner');
  const btn2Space = document.getElementById('btn-json-2space');
  const btn4Space = document.getElementById('btn-json-4space');
  const btnMinify = document.getElementById('btn-json-minify');
  const btnSample = document.getElementById('btn-json-sample');
  const btnClear = document.getElementById('btn-json-clear');

  function showStatus(message, isError) {
    if (!statusBanner) return;
    statusBanner.style.display = 'block';
    statusBanner.style.backgroundColor = isError ? 'var(--danger-bg)' : 'var(--success-bg)';
    statusBanner.style.color = isError ? 'var(--danger)' : 'var(--success)';
    statusBanner.style.border = `1px solid ${isError ? 'var(--danger)' : 'var(--success)'}`;
    statusBanner.textContent = message;
  }

  function hideStatus() {
    if (statusBanner) statusBanner.style.display = 'none';
  }

  function formatJSON(indent) {
    const raw = input.value.trim();
    if (!raw) {
      hideStatus();
      return;
    }
    try {
      const parsed = JSON.parse(raw);
      input.value = indent === 0 ? JSON.stringify(parsed) : JSON.stringify(parsed, null, indent);
      showStatus('✓ Valid JSON formatted successfully.', false);
    } catch (err) {
      showStatus(`Syntax Error: ${err.message}`, true);
    }
  }

  if (btn2Space) btn2Space.addEventListener('click', () => formatJSON(2));
  if (btn4Space) btn4Space.addEventListener('click', () => formatJSON(4));
  if (btnMinify) btnMinify.addEventListener('click', () => formatJSON(0));

  if (btnSample) {
    btnSample.addEventListener('click', () => {
      const sample = {
        website: "ToolNest",
        version: "1.0",
        features: ["100% Free", "Zero Cold Start", "Private Processing"],
        tools: {
          browser: ["word-counter", "case-converter", "json-formatter", "emi-calculator", "sip-calculator", "gst-calculator"],
          server: ["merge-pdf", "compress-pdf", "split-pdf", "qr-code-generator"]
        },
        active: true
      };
      input.value = JSON.stringify(sample, null, 2);
      showStatus('✓ Sample JSON loaded.', false);
    });
  }

  if (btnClear) {
    btnClear.addEventListener('click', () => {
      input.value = '';
      hideStatus();
      input.focus();
    });
  }

  input.addEventListener('input', () => {
    if (!input.value.trim()) hideStatus();
  });
}

// -------------------------------------------------------------
// 4. EMI Calculator
// -------------------------------------------------------------
function initEmiCalculator() {
  const amountSlider = document.getElementById('emi-amount');
  const amountInput = document.getElementById('emi-amount-input');
  const rateSlider = document.getElementById('emi-rate');
  const rateInput = document.getElementById('emi-rate-input');
  const tenureSlider = document.getElementById('emi-tenure');
  const tenureInput = document.getElementById('emi-tenure-input');

  if (!amountSlider || !rateSlider || !tenureSlider) return;

  const resultMonthly = document.getElementById('emi-result-monthly');
  const resultPrincipal = document.getElementById('emi-result-principal');
  const resultInterest = document.getElementById('emi-result-interest');
  const resultTotal = document.getElementById('emi-result-total');
  const barPrincipal = document.getElementById('emi-bar-principal');
  const barInterest = document.getElementById('emi-bar-interest');
  const barPrincipalLabel = document.getElementById('emi-bar-principal-label');
  const barInterestLabel = document.getElementById('emi-bar-interest-label');

  function sync(slider, input) {
    slider.addEventListener('input', () => {
      input.value = slider.value;
      calculateEMI();
    });
    input.addEventListener('input', () => {
      let val = parseFloat(input.value);
      if (isNaN(val)) return;
      slider.value = Math.min(Math.max(val, parseFloat(slider.min)), parseFloat(slider.max));
      calculateEMI();
    });
  }

  sync(amountSlider, amountInput);
  sync(rateSlider, rateInput);
  sync(tenureSlider, tenureInput);

  function calculateEMI() {
    const P = parseFloat(amountInput.value) || 0;
    const annualRate = parseFloat(rateInput.value) || 0;
    const years = parseFloat(tenureInput.value) || 0;

    const r = (annualRate / 12) / 100;
    const n = years * 12;

    let emi = 0;
    let totalPayment = 0;
    let totalInterest = 0;

    if (P > 0 && r > 0 && n > 0) {
      emi = Math.round((P * r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1));
      totalPayment = Math.round(emi * n);
      totalInterest = Math.max(0, totalPayment - P);
    } else if (P > 0 && n > 0 && r === 0) {
      emi = Math.round(P / n);
      totalPayment = P;
      totalInterest = 0;
    }

    if (resultMonthly) resultMonthly.textContent = formatCurrency(emi);
    if (resultPrincipal) resultPrincipal.textContent = formatCurrency(P);
    if (resultInterest) resultInterest.textContent = formatCurrency(totalInterest);
    if (resultTotal) resultTotal.textContent = formatCurrency(totalPayment);

    // Percentage breakdown bar
    if (totalPayment > 0) {
      const principalPct = Math.round((P / totalPayment) * 100);
      const interestPct = 100 - principalPct;

      if (barPrincipal) barPrincipal.style.width = `${principalPct}%`;
      if (barInterest) barInterest.style.width = `${interestPct}%`;
      if (barPrincipalLabel) barPrincipalLabel.textContent = `Principal (${principalPct}%)`;
      if (barInterestLabel) barInterestLabel.textContent = `Interest (${interestPct}%)`;
    }
  }

  calculateEMI();
}

// -------------------------------------------------------------
// 5. SIP Calculator
// -------------------------------------------------------------
function initSipCalculator() {
  const amountSlider = document.getElementById('sip-amount');
  const amountInput = document.getElementById('sip-amount-input');
  const rateSlider = document.getElementById('sip-rate');
  const rateInput = document.getElementById('sip-rate-input');
  const yearsSlider = document.getElementById('sip-years');
  const yearsInput = document.getElementById('sip-years-input');

  if (!amountSlider || !rateSlider || !yearsSlider) return;

  const resultTotal = document.getElementById('sip-result-total');
  const resultInvested = document.getElementById('sip-result-invested');
  const resultReturns = document.getElementById('sip-result-returns');
  const barInvested = document.getElementById('sip-bar-invested');
  const barReturns = document.getElementById('sip-bar-returns');
  const barInvestedLabel = document.getElementById('sip-bar-invested-label');
  const barReturnsLabel = document.getElementById('sip-bar-returns-label');

  function sync(slider, input) {
    slider.addEventListener('input', () => {
      input.value = slider.value;
      calculateSIP();
    });
    input.addEventListener('input', () => {
      let val = parseFloat(input.value);
      if (isNaN(val)) return;
      slider.value = Math.min(Math.max(val, parseFloat(slider.min)), parseFloat(slider.max));
      calculateSIP();
    });
  }

  sync(amountSlider, amountInput);
  sync(rateSlider, rateInput);
  sync(yearsSlider, yearsInput);

  function calculateSIP() {
    const P = parseFloat(amountInput.value) || 0;
    const annualRate = parseFloat(rateInput.value) || 0;
    const years = parseFloat(yearsInput.value) || 0;

    const i = (annualRate / 12) / 100;
    const n = years * 12;

    let futureValue = 0;
    const invested = Math.round(P * n);

    if (P > 0 && n > 0) {
      if (i > 0) {
        futureValue = Math.round(P * ((Math.pow(1 + i, n) - 1) / i) * (1 + i));
      } else {
        futureValue = invested;
      }
    }

    const returns = Math.max(0, futureValue - invested);

    if (resultTotal) resultTotal.textContent = formatCurrency(futureValue);
    if (resultInvested) resultInvested.textContent = formatCurrency(invested);
    if (resultReturns) resultReturns.textContent = formatCurrency(returns);

    if (futureValue > 0) {
      const investedPct = Math.min(100, Math.round((invested / futureValue) * 100));
      const returnsPct = 100 - investedPct;

      if (barInvested) barInvested.style.width = `${investedPct}%`;
      if (barReturns) barReturns.style.width = `${returnsPct}%`;
      if (barInvestedLabel) barInvestedLabel.textContent = `Invested (${investedPct}%)`;
      if (barReturnsLabel) barReturnsLabel.textContent = `Returns (${returnsPct}%)`;
    }
  }

  calculateSIP();
}

// -------------------------------------------------------------
// 6. GST Calculator
// -------------------------------------------------------------
function initGstCalculator() {
  const amountInput = document.getElementById('gst-amount');
  if (!amountInput) return;

  const resultTotal = document.getElementById('gst-result-total');
  const resultNet = document.getElementById('gst-result-net');
  const resultTax = document.getElementById('gst-result-tax');
  const resultCgst = document.getElementById('gst-result-cgst');
  const resultSgst = document.getElementById('gst-result-sgst');

  function getSelectedRate() {
    const selected = document.querySelector('input[name="gst-rate"]:checked');
    return selected ? parseFloat(selected.value) || 0 : 18;
  }

  function getMode() {
    const selected = document.querySelector('input[name="gst-type"]:checked');
    return selected ? selected.value : 'add';
  }

  function calculateGST() {
    const amount = parseFloat(amountInput.value) || 0;
    const rate = getSelectedRate();
    const mode = getMode();

    let netAmount = 0;
    let gstAmount = 0;
    let totalGross = 0;

    if (mode === 'add') {
      // Exclusive: Amount is base amount, add GST on top
      netAmount = amount;
      gstAmount = amount * (rate / 100);
      totalGross = amount + gstAmount;
    } else {
      // Inclusive: Amount includes GST, calculate base amount
      netAmount = amount / (1 + (rate / 100));
      gstAmount = amount - netAmount;
      totalGross = amount;
    }

    const halfTax = gstAmount / 2;

    if (resultTotal) resultTotal.textContent = formatCurrency(totalGross, 2);
    if (resultNet) resultNet.textContent = formatCurrency(netAmount, 2);
    if (resultTax) resultTax.textContent = formatCurrency(gstAmount, 2);
    if (resultCgst) resultCgst.textContent = formatCurrency(halfTax, 2);
    if (resultSgst) resultSgst.textContent = formatCurrency(halfTax, 2);
  }

  amountInput.addEventListener('input', calculateGST);

  document.querySelectorAll('input[name="gst-rate"]').forEach(r => {
    r.addEventListener('change', calculateGST);
  });

  document.querySelectorAll('input[name="gst-type"]').forEach(r => {
    r.addEventListener('change', calculateGST);
  });

  calculateGST();
}

// -------------------------------------------------------------
// Global Initialization on DOM Ready
// -------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  initWordCounter();
  initCaseConverter();
  initJsonFormatter();
  initEmiCalculator();
  initSipCalculator();
  initGstCalculator();
});
