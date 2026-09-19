function validEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
}
if (typeof module !== 'undefined') module.exports = { validEmail };
if (typeof document !== 'undefined') {
  const form = document.querySelector('#signup');
  form.addEventListener('submit', event => {
    event.preventDefault();
    const value = document.querySelector('#email').value;
    const message = document.querySelector('#message');
    if (!validEmail(value)) {
      message.textContent = 'Проверьте адрес почты';
      return;
    }
    document.querySelector('#subscription-message').textContent = 'Вы подписаны!';
  });
}
