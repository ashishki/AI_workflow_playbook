'use strict';

const form = document.querySelector('#request-form');
const nameInput = document.querySelector('#name');
const emailInput = document.querySelector('#email');
const courseInput = document.querySelector('#course');
const status = document.querySelector('#form-status');
const resetButton = document.querySelector('#reset-form');

function showError(input, message) {
  const error = document.querySelector(`#${input.id}-error`);
  error.textContent = message;
  error.hidden = !message;
  input.setAttribute('aria-invalid', message ? 'true' : 'false');
}

function validate(input) {
  const value = input.value.trim();
  let message = '';
  if (input === nameInput && value.length < 2) {
    message = 'Напишите имя: хотя бы два символа.';
  }
  if (input === emailInput && (!value || !input.validity.valid)) {
    message = 'Укажите email в формате sasha@example.com.';
  }
  showError(input, message);
  return !message;
}

[nameInput, emailInput].forEach(input => {
  input.addEventListener('input', () => {
    if (input.getAttribute('aria-invalid') === 'true') validate(input);
  });
});

function openForm() {
  form.hidden = false;
  resetButton.hidden = true;
  status.textContent = '';
}

document.querySelectorAll('[data-course]').forEach(button => {
  button.addEventListener('click', () => {
    openForm();
    courseInput.value = button.dataset.course;
    document.querySelector('#request').scrollIntoView({ block: 'start' });
    nameInput.focus({ preventScroll: true });
  });
});

form.addEventListener('submit', event => {
  event.preventDefault();
  const nameValid = validate(nameInput);
  const emailValid = validate(emailInput);
  if (!nameValid || !emailValid) {
    (!nameValid ? nameInput : emailInput).focus();
    return;
  }
  form.hidden = true;
  status.textContent = `${nameInput.value.trim()}, учебная заявка заполнена! Это демонстрация: данные никуда не отправлены, преподаватель не получит заявку. Можно заполнить форму ещё раз.`;
  resetButton.hidden = false;
  resetButton.focus();
});

resetButton.addEventListener('click', () => {
  form.reset();
  [nameInput, emailInput].forEach(input => showError(input, ''));
  openForm();
  nameInput.focus();
});

// This local example deliberately has no network requests or persistent storage.
window.addEventListener('pageshow', () => {
  form.reset();
  [nameInput, emailInput].forEach(input => showError(input, ''));
  openForm();
});
