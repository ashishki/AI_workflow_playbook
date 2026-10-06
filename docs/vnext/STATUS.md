# Playbook — текущая работа после объединения vNext

Проверенная исходная точка программы delivery: master
`0c4027f8ecfc0b086c39613bb8c83a91b962d139`, merge PR #9 от 20 сентября 2026.
Рабочая ветка: `feature/playbook-delivery-20260920`.

Новая программа: [D00–D10](../delivery/PLAN_RU.md).
Desktop source slice: [DESKTOP_SETUP_PREVIEW_RU.md](../delivery/DESKTOP_SETUP_PREVIEW_RU.md).
VPS/owner acceptance: [VPS_ACCEPTANCE_RU.md](../delivery/VPS_ACCEPTANCE_RU.md).

## Что уже есть в ветке как исходники

Engineering/Product/Shared, 13 lifecycle-процедур, solution record, Native kit,
preview/share gates и delivery tests уже существовали. 6 октября добавлен source
slice для OS-specific Desktop setup: управляемое подключение/обновление/удаление,
installation rollback, frozen helper, optional pinned per-user Codex runtime и
Windows/macOS/Linux build matrix.

Последние небольшие уточнения Product из master — outcome hypothesis в Discover и
decision-boundary checks в Verify — также должны входить в delivery-ветку перед merge.

## Что не считается принятым

Владелец намеренно будет прогонять exact commit после push. Поэтому source code,
unit tests и CI definition не получают PASS заранее.

До фактического исполнения остаются pending:
- полный suite и matrix CI exact commit;
- три OS-specific frozen artifacts;
- clean-machine setup на Windows/macOS/Linux;
- реальный Codex login/reviewer и browser path;
- пользовательский Product-проход, повторное изменение и transfer;
- права распространения/signing/notarization;
- бизнес-эффект.

Исторические CI/review/model runs не переносятся автоматически на новый desktop
slice. Master, downstream, production, аккаунты и права не меняются этой веткой.

Следующий шаг владельца после push: прогнать CI/локальные проверки, скачать exact
artifacts, выполнить clean-machine trials и только затем решить merge.
