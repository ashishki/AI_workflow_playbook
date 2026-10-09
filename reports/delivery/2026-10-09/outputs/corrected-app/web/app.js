"use strict";
const teacher = document.querySelector("#teacher");
const form = document.querySelector("#booking-form");
const formStatus = document.querySelector("#form-status");
const listStatus = document.querySelector("#list-status");
const bookings = document.querySelector("#bookings");
const submit = document.querySelector("#submit");
let generation = 0;
function status(node, text, kind = "") { node.textContent = text; node.className = "status " + kind; }
async function api(path, identity, options = {}) {
  let response;
  try { response = await fetch(path, {...options, headers: {"X-Teacher": identity, "Content-Type": "application/json"}}); }
  catch (_) { throw new Error("Нет связи с локальным сервером. Повторите запрос с теми же данными."); }
  let data;
  try { data = await response.json(); } catch (_) { throw new Error("Сервер вернул неожиданный ответ. Повторите запрос с теми же данными."); }
  if (!response.ok) throw new Error(data.error || "Запрос не выполнен.");
  return data;
}
async function loadBookings() {
  const identity = teacher.value, current = ++generation;
  bookings.replaceChildren(); document.querySelector("#count").textContent = "0";
  status(listStatus, "Загрузка записей…");
  document.querySelector("#identity-note").textContent = "Показаны только записи " + (identity === "anna" ? "Анны" : "Бориса");
  try {
    const data = await api("/api/bookings", identity);
    if (current !== generation || identity !== teacher.value) return;
    document.querySelector("#count").textContent = String(data.bookings.length);
    status(listStatus, "");
    if (!data.bookings.length) { const empty = document.createElement("li"); empty.className = "empty"; empty.textContent = "Пока нет записей. Создайте первое занятие."; bookings.append(empty); }
    for (const booking of data.bookings) {
      const li = document.createElement("li"), time = document.createElement("div"), detail = document.createElement("div"), name = document.createElement("div"), date = document.createElement("div");
      li.className = "booking"; time.className = "booking-time"; name.className = "booking-name"; date.className = "booking-date";
      time.textContent = booking.slot; name.textContent = booking.student;
      date.textContent = booking.date.split("-").reverse().join(".");
      detail.append(name, date); li.append(time, detail); bookings.append(li);
    }
  } catch (error) { if (current === generation) status(listStatus, error.message, "error"); }
}
teacher.addEventListener("change", () => { status(formStatus, ""); loadBookings(); });
document.querySelector("#refresh").addEventListener("click", loadBookings);
form.addEventListener("submit", async event => {
  event.preventDefault();
  const identity = teacher.value;
  const payload = {student: form.student.value.trim(), date: form.date.value, slot: form.slot.value};
  if (!payload.student || !payload.date || !payload.slot) { status(formStatus, "Заполните имя, дату и время занятия.", "error"); return; }
  const key = "booking-demo-pending:" + JSON.stringify([identity, payload.student, payload.date, payload.slot]);
  // Keep the same id after uncertain network outcome, including a page reload.
  payload.request_id = sessionStorage.getItem(key) || crypto.randomUUID();
  sessionStorage.setItem(key, payload.request_id);
  submit.disabled = true; status(formStatus, "Сохраняем запись…");
  try {
    const data = await api("/api/bookings", identity, {method: "POST", body: JSON.stringify(payload)});
    sessionStorage.removeItem(key);
    if (identity === teacher.value) { status(formStatus, data.replayed ? "Запись уже сохранена; повтор не создал дубликат." : "Запись создана.", "success"); form.reset(); await loadBookings(); }
  } catch (error) { if (identity === teacher.value) status(formStatus, error.message, "error"); }
  finally { submit.disabled = false; }
});
loadBookings();
