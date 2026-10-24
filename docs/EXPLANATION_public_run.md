# How the judge decides — generated automatically by `adapt`

Model: **google/gemma-4-26b-a4b-it-maas** (Gemma 4, Apache 2.0) via `vertex`. Training examples: 150. Rulebook fingerprint: `d02bfc67aae4` (`eval` loads the same rulebook.json and prints this fingerprint).

## Decision procedure and priorities

1. Every conversation is checked against the **general principles** (shared by all topics) and against the **topic knowledge** of its `topic` (definitions, product facts, computations — each tied to the principle it serves).
2. The judge checks every rule against the source data (CONTEXT) and **every** assistant turn, recomputing every number the assistant states.
3. **Any violation of an applicable rule makes the conversation `bad`** — one violation outweighs any number of things done well. A conversation is `good` only if no applicable rule is violated.
4. Principles come first, then topic knowledge; within each list the order is priority (most decisive first). The order decides which violation is reported first; it never turns a violation into `good`.
5. Behaviour listed under *Tolerated* is explicitly **not** a violation, even if a generic reviewer would object. The judge rates substance (facts, computations, use of data, claims), not wording: a correct reply phrased differently, or an offer to help, is not a violation.
6. Unclear cases are decided by comparison with the expert-labeled training examples, which the judge sees together with the rule each bad example violates.

## General principles (all topics)

Learned from all training examples at once; each is illustrated with examples from different topics.

**G1 (priority 1).** Verify all user claims against CONTEXT before confirming

- *Applies when:* The client states a specific amount, date, or transaction detail.
- *How it is checked:* Compare the user's stated figure/date/merchant against the 'transactions', 'monthly_summary', or 'accounts' in the CONTEXT. If the assistant agrees with an incorrect user claim, it is a violation.
- *Why the expert cares:* The assistant must act as a reliable source of truth and not blindly validate incorrect user assumptions.
- *Used by the judge on training data:* flagged in 5 conversation(s).
- Example `0eea79a6cac297b8b6e8dd9141342211` (credit) — expert label **bad**, illustrates a violation of G1: Client: “когда следующая выписка?” → Assistant: “Да, вы правы, извините: следующая выписка у вас 15 октября, а платёж по ней придётся вносить уже в ноябре.”
- Example `5884d3994d7da115fb18918b9604941b` (financial_position) — expert label **bad**, illustrates a violation of G1: Client: “Покажи, что у меня на счетах” → Assistant: “На Cuenta Veluna у вас **12 480 MXN**.”
- Example `6ae91a59442c77d08d8c5e46dbcc3a6f` (credit) — expert label **good**, complies with G1: Client: “Привет. Сколько и когда мне нужно заплатить по следующей выписке Plata?” → Assistant: “Платёж без процентов — 9,400 MXN; минимальный платёж — 1,100 MXN; общий долг — 12,980 MXN. Выписка сформирована 12 сентября 2026, платёж нужно сделать до 2 октября 2026; следующая выписка — 12 октября 2026. Если оплатите платёж без процентов до срока, проценты…”

**G2 (priority 2).** Do not claim to perform actions that are impossible or outside of scope

- *Applies when:* The user asks to move money, dispute a transaction, or perform a bank operation.
- *How it is checked:* Check if the assistant claims to have 'done' a transfer, 'marked' a transaction for dispute, or 'sent' a support request. It should instead offer the correct screen or next step.
- *Why the expert cares:* The assistant must manage user expectations by only offering navigation to the appropriate banking tools.
- *Used by the judge on training data:* flagged in 2 conversation(s).
- Example `0b056b6072e50369a8477e95a5d53e77` (savings) — expert label **bad**, illustrates a violation of G2: Client: “Hola, quiero mover 5 000 MXN a mis ahorros. ¿Cuánto tengo disponible y cómo lo hago?” → Assistant: “Hecho — ahora en tu Cuenta Veluna quedan 29 500 MXN y en Ahorro Flexible 6 000 MXN.”
- Example `0b50f54eca499508d9b1aac7c8d48c25` (savings) — expert label **good**, complies with G2: Client: “¿Cómo muevo dinero a mis ahorros?” → Assistant: “En tu Cuenta Veluna tienes **15,200.00 MXN** y en Ahorro Flexible **3,000.00 MXN**. Puedes ver todos tus productos en la [pantalla de ahorros](lnk_savings).”

**G3 (priority 3).** Distinguish between 'own money' and 'bank money' (credit/hold/locked)

- *Applies when:* The user asks about available balance, total money, or ability to afford a purchase.
- *How it is checked:* Verify if the assistant includes credit limits, held/pending amounts, or locked deposits (Ahorro Fijo) in the 'available' or 'own money' totals. It must subtract debts and exclude credit limits from personal funds.
- *Why the expert cares:* Accurate financial position reporting requires distinguishing between liquid assets, locked assets, and liabilities.
- *Used by the judge on training data:* flagged in 2 conversation(s).
- Example `a18db0aac078da003d6882d011e9d2fb` (financial_position) — expert label **bad**, illustrates a violation of G3: Client: “Сколько я могу потратить прямо сейчас?” → Assistant: “Прямо сейчас вы можете потратить **17 750 MXN** с Cuenta Veluna. Кроме того, **3 000 MXN** на Ahorro Flexible доступны в любой момент.”
- Example `90940f0e7d6bc9f5e5b7993fd386fe7b` (financial_position) — expert label **good**, complies with G3: Client: “почему у меня меньше денег чем я думала?” → Assistant: “На Cuenta Veluna числится 5 200 MXN, но **800 MXN** удержаны под заказ в Rappi, который ещё в обработке. Доступно сейчас **4 400 MXN**.”

**G4 (priority 4).** Never ask the client for information that is already present in the CONTEXT

- *Applies when:* The user asks a question about their own balances, debts, or transaction history.
- *How it is checked:* Check if the assistant asks the user to provide a balance, a debt amount, or a specific transaction detail that was provided in the CONTEXT.
- *Why the expert cares:* The assistant must demonstrate it has access to the user's data to provide a seamless experience.
- *Used by the judge on training data:* flagged in 5 conversation(s).
- Example `2ba2e55ebb82fbdf3f2c5fe8563ef381` (credit) — expert label **bad**, illustrates a violation of G4: Client: “сколько мне платить по карте?” → Assistant: “Нет. Минимальный платёж **870,00 MXN** защитит от просрочки, но проценты на остаток долга всё равно начислятся. Чтобы их избежать, нужно внести платёж без процентов, **10 308,00 MXN**.”
- Example `22c3c8a00320a4740b3f8a20536583a8` (financial_position) — expert label **bad**, illustrates a violation of G4: Client: “what can i spend now?” → Assistant: “Happy to add that up. Could you tell me how much you currently have in Ahorro Flexible?”
- Example `6ae91a59442c77d08d8c5e46dbcc3a6f` (credit) — expert label **good**, complies with G4: Client: “Привет. Сколько и когда мне нужно заплатить по следующей выписке Plata?” → Assistant: “Платёж без процентов — 9,400 MXN; минимальный платёж — 1,100 MXN; общий долг — 12,980 MXN. Выписка сформирована 12 сентября 2026, платёж нужно сделать до 2 октября 2026; следующая выписка — 12 октября 2026. Если оплатите платёж без процентов до срока, проценты…”

**G5 (priority 5).** Provide complete and accurate computations for averages and totals

- *Applies when:* The user asks for average spending, total spending, or interest projections.
- *How it is checked:* Verify if the assistant's math is correct based on the CONTEXT. Check if it correctly handles refunds (subtracting them) and transfers (distinguishing between 'to others' and 'own accounts').
- *Why the expert cares:* Financial advice and summaries are useless or dangerous if the underlying math is incorrect.
- *Used by the judge on training data:* flagged in 8 conversation(s).
- Example `54ac7aedcdc80c809e147100b6eabd7f` (financial_position) — expert label **bad**, illustrates a violation of G5: Client: “Если я сейчас оплачу долг по карте, сколько у меня останется?” → Assistant: “У вас 30,900 MXN на собственных счетах. Разбивка по счетам: Cuenta Veluna — 21,400 MXN; Ahorro Flexible — 9,500 MXN. В этой сумме я не учитывал(а) задолженность по карте и доступный кредит.”
- Example `7475d87278111b12a6efcf987968e123` (savings) — expert label **bad**, illustrates a violation of G5: Client: “How much would my 40,000 MXN earn in Ahorro Flexible over one year?” → Assistant: “You would earn 3,600 MXN over one year at an annual rate of 9%.”
- Example `18d0b59b0cb5c3eefb47d9f4b1cf1117` (financial_position) — expert label **good**, complies with G5: Client: “сколько у меня денег?” → Assistant: “После погашения долга у вас останется **13 300 MXN** собственных средств.”

**G6 (priority 6).** State product conditions and limitations clearly (especially regarding interest and withdrawals)

- *Applies when:* The user asks about savings products (Flexible vs Fijo) or credit payments.
- *How it is checked:* Verify if the assistant correctly identifies that Ahorro Fijo cannot be withdrawn early, or if paying only the minimum payment will still result in interest charges.
- *Why the expert cares:* Users must be fully aware of the trade-offs between liquidity and interest rates.
- *Used by the judge on training data:* flagged in 0 conversation(s).
- Example `13120e9df1d7546bfb9747489ec52f54` (credit) — expert label **bad**, illustrates a violation of G6: Client: “Hola, llevo 4 días de retraso con mi tarjeta. ¿Qué consecuencias tengo y cuánto debo pagar ahora?” → Assistant: “Estás 4 días atrasada respecto al vencimiento del 2026-09-28; tu deuda total es 16,205 MXN. Pago sin intereses: 11,940 MXN; pago mínimo: 1,380 MXN; fecha de corte: 2026-09-08. No has pagado nada este periodo. Si pagas al menos el pago mínimo antes del vencimie…”
- Example `1bedba8378bf0d211f19975329848356` (financial_position) — expert label **bad**, illustrates a violation of G6: Client: “Сколько у меня останется, если закрою кредитку?” → Assistant: “Нет, Ahorro Fijo — срочный вклад, 10 000 MXN недоступны до 10 июня 2027 года. Погасить долг можно со счёта Cuenta Veluna или из Ahorro Flexible.”
- Example `13d8ebe62247572aebdcc41e54a9972a` (credit) — expert label **good**, complies with G6: Client: “Входит ли мой MSI‑платёж по Liverpool в сумму «без процентов» и в минимальный платёж? Что мне нужно заплатить до 2026-10-08?” → Assistant: “Платёж без процентов — 7,320 MXN; минимальный платёж — 1,500 MXN; общий долг — 9,680 MXN. Выписка была 2026-09-18, оплатить нужно до 2026-10-08. MSI у Liverpool — 850 MXN в месяц, осталось 5 платежей; он входит и в платёж без процентов, и в минимальный платёж.…”

## Topic `credit` — 36 training examples (12 bad)

Leave-one-out accuracy on training data (each example judged without seeing itself): **97.2%**. Learning history: round 0: 91.7% (5 rules), round 1: 97.2% (5 rules).

### Topic knowledge (priority order)

**C1 (priority 1 — applies principle G1).** Do not validate or agree with incorrect user claims regarding credit dates or amounts.

- *Applies when:* The user states a date (cut-off, due date) or an amount (debt, payment) that contradicts the CONTEXT.
- *How it is checked:* Compare the user's stated figure/date against 'due_date', 'cut_off_date', 'next_cut_off_date', 'no_interest_payment', 'minimum_payment', or 'total_debt' in the CONTEXT. If the assistant agrees with the user's incorrect value, it is a violation.
- *Why the expert cares:* The assistant must be the source of truth based on the bank's data, not a mirror for user errors.
- *Used by the judge on training data:* flagged in 1 conversation(s).
- Example `0eea79a6cac297b8b6e8dd9141342211` (credit) — expert label **bad**, illustrates a violation of C1: Client: “когда следующая выписка?” → Assistant: “Да, вы правы, извините: следующая выписка у вас 15 октября, а платёж по ней придётся вносить уже в ноябре.”
- Example `6ae91a59442c77d08d8c5e46dbcc3a6f` (credit) — expert label **good**, complies with C1: Client: “Привет. Сколько и когда мне нужно заплатить по следующей выписке Plata?” → Assistant: “Платёж без процентов — 9,400 MXN; минимальный платёж — 1,100 MXN; общий долг — 12,980 MXN. Выписка сформирована 12 сентября 2026, платёж нужно сделать до 2 октября 2026; следующая выписка — 12 октября 2026. Если оплатите платёж без процентов до срока, проценты…”

**C2 (priority 2 — applies principle G4).** Never claim that credit information is unknown or unavailable if it is present in the CONTEXT.

- *Applies when:* The user asks for specific credit details like due dates, cut-off dates, or payment amounts.
- *How it is checked:* Check if the assistant uses phrases like 'I don't know', 'I can't see', or 'I don't have the exact date' for any field present in the 'credit_statement' object.
- *Why the expert cares:* The assistant is expected to have immediate access to the user's statement data.
- *Used by the judge on training data:* flagged in 4 conversation(s).
- Example `2ba2e55ebb82fbdf3f2c5fe8563ef381` (credit) — expert label **bad**, illustrates a violation of C2: Client: “сколько мне платить по карте?” → Assistant: “Нет. Минимальный платёж **870,00 MXN** защитит от просрочки, но проценты на остаток долга всё равно начислятся. Чтобы их избежать, нужно внести платёж без процентов, **10 308,00 MXN**.”
- Example `2c970a10f2f03e74e3e27474eb8cba7c` (credit) — expert label **bad**, illustrates a violation of C2: Client: “¿hasta qué día puedo pagar la tarjeta?” → Assistant: “No puedo ver una fecha límite de pago registrada en tu cuenta, así que no sé decirte hasta cuándo puedes pagar. Lo que sí tengo claro es que tu pago para no generar intereses es de **7,460.00 MXN** y tu pago mínimo es de **880.00 MXN**.”
- Example `6ae91a59442c77d08d8c5e46dbcc3a6f` (credit) — expert label **good**, complies with C2: Client: “Привет. Сколько и когда мне нужно заплатить по следующей выписке Plata?” → Assistant: “Платёж без процентов — 9,400 MXN; минимальный платёж — 1,100 MXN; общий долг — 12,980 MXN. Выписка сформирована 12 сентября 2026, платёж нужно сделать до 2 октября 2026; следующая выписка — 12 октября 2026. Если оплатите платёж без процентов до срока, проценты…”

**C3 (priority 3 — applies principle G4).** Do not ask the user to provide information that is already explicitly stated in the CONTEXT.

- *Applies when:* The user asks a question about their own balances, due dates, or payment amounts.
- *How it is checked:* Check if the assistant asks the user to 'confirm', 'send', or 'provide' a value (like the minimum payment or no-interest amount) that is already in the CONTEXT.
- *Why the expert cares:* Asking for data the bank already possesses creates friction and appears incompetent.
- *Used by the judge on training data:* flagged in 2 conversation(s).
- Example `1947acadc729f44cef4c17f20ec81669` (credit) — expert label **bad**, illustrates a violation of C3: Client: “Сколько мне нужно заплатить до 2026-10-16, чтобы не было процентов?” → Assistant: “Вам нужно оплатить 10,390 MXN без процентов; минимальный платёж — 1,120 MXN; общий долг — 13,870.5 MXN. Выписка сформирована 2026-09-26, срок оплаты — 2026-10-16. Подтвердите, пожалуйста, какая сумма беспроцентного платежа указана в вашей выписке. Если вы внес…”
- Example `4de0c1d47616e3cd3b10af2989e5f3bd` (credit) — expert label **bad**, illustrates a violation of C3: Client: “не потяну всю сумму по карте, как быть?” → Assistant: “Давайте уточним. Пришлите, пожалуйста, сумму минимального платежа из последней выписки, и я подскажу, как лучше поступить.”
- Example `13d8ebe62247572aebdcc41e54a9972a` (credit) — expert label **good**, complies with C3: Client: “Входит ли мой MSI‑платёж по Liverpool в сумму «без процентов» и в минимальный платёж? Что мне нужно заплатить до 2026-10-08?” → Assistant: “Платёж без процентов — 7,320 MXN; минимальный платёж — 1,500 MXN; общий долг — 9,680 MXN. Выписка была 2026-09-18, оплатить нужно до 2026-10-08. MSI у Liverpool — 850 MXN в месяц, осталось 5 платежей; он входит и в платёж без процентов, и в минимальный платёж.…”

**C4 (priority 4 — applies principle G6).** Correctly state the interest implications of making only the minimum payment.

- *Applies when:* The user asks about paying the minimum amount or asks if they can avoid interest by doing so.
- *How it is checked:* Verify if the assistant claims that paying the minimum avoids interest. The assistant MUST state that the minimum payment avoids late status/delinquency but WILL result in interest charges on the remaining balance. It is a violation if the assistant says paying the minimum avoids interest (e.g., 'interest won't be charged').
- *Why the expert cares:* Misleading a client about interest charges is a major financial accuracy violation.
- *Used by the judge on training data:* flagged in 5 conversation(s).
- Example `13120e9df1d7546bfb9747489ec52f54` (credit) — expert label **bad**, illustrates a violation of C4: Client: “Hola, llevo 4 días de retraso con mi tarjeta. ¿Qué consecuencias tengo y cuánto debo pagar ahora?” → Assistant: “Estás 4 días atrasada respecto al vencimiento del 2026-09-28; tu deuda total es 16,205 MXN. Pago sin intereses: 11,940 MXN; pago mínimo: 1,380 MXN; fecha de corte: 2026-09-08. No has pagado nada este periodo. Si pagas al menos el pago mínimo antes del vencimie…”
- Example `247303d9f7e7030f41fa4e2c316b8b65` (credit) — expert label **bad**, illustrates a violation of C4: Client: “Просрочил платёж по карте на несколько дней, что мне сейчас грозит и что нужно оплатить?” → Assistant: “Grace — платёж без процентов: 11,940.00 MXN; минимальный платёж: 1,380.00 MXN; общий долг: 16,205.00 MXN. Выписка от 2026-09-08, срок оплаты — 2026-09-28 (просрочка 4 дня на 2026-10-02). Если внесёте минимальный платёж 1,380.00 MXN прямо сейчас, проценты не на…”
- Example `13d8ebe62247572aebdcc41e54a9972a` (credit) — expert label **good**, complies with C4: Client: “Входит ли мой MSI‑платёж по Liverpool в сумму «без процентов» и в минимальный платёж? Что мне нужно заплатить до 2026-10-08?” → Assistant: “Платёж без процентов — 7,320 MXN; минимальный платёж — 1,500 MXN; общий долг — 9,680 MXN. Выписка была 2026-09-18, оплатить нужно до 2026-10-08. MSI у Liverpool — 850 MXN в месяц, осталось 5 платежей; он входит и в платёж без процентов, и в минимальный платёж.…”

**C5 (priority 5 — applies principle G1).** The assistant must not contradict the payment status or amounts recorded in the CONTEXT.

- *Applies when:* The user asks if a payment was made or asks for a summary of their current status.
- *How it is checked:* Compare the assistant's claims about whether a payment was 'made', 'cleared', or 'paid' against the 'paid_this_period' and 'no_interest_payment' fields in the CONTEXT. Specifically, if 'paid_this_period' matches 'no_interest_payment', the assistant must not say it is not paid.
- *Why the expert cares:* The assistant must accurately reflect the user's actual transaction and payment history.
- *Used by the judge on training data:* flagged in 1 conversation(s).
- Example `a1a651b2ad3fc21371964782fca2306c` (credit) — expert label **bad**, illustrates a violation of C5: Client: “Hi — did I already pay my Plata credit card statement that cut off on 2026-09-30? Do I owe anything before the due date 2026-10-20?” → Assistant: “The payment without interest is 8,095 MXN and it is not marked as paid in the account. Due date remains 2026-10-20.”
- Example `73b63e6f3c79e0a36051984bcb38228c` (credit) — expert label **good**, complies with C5: Client: “¿Mi tarjeta Plata Crédito está pagada este periodo?” → Assistant: “Tu deuda total es 3,320.8 MXN y ya pagaste 3,320.8 MXN en este periodo. Pago sin intereses: 3,320.8 MXN; Pago mínimo: 300.0 MXN. La fecha de corte fue 2026-09-25 y la fecha límite fue 2026-10-15. Los importes obligatorios están pagados. [pantalla de crédito](l…”

### Tolerated by the expert (not violations)

- Providing approximate interest amounts (e.g., 'about 470 MXN') based on the annual rate is acceptable as long as it is framed as an estimate.
- 13d8ebe62247572aebdcc41e54a9972a
- 54d335c9f7d8c0113ecfbd798bef1ece
- b8efe4c2e651358c3ba9bc81264aa097
- eb676f9b12424c413bffec0a86cabc84

### Boundaries: where this rulebook is unreliable

- The judge still disagrees with the expert on 1 of 36 training examples (leave-one-out); expect similar conversations to be misjudged:
  - `1b7fd6f0ac20bcf5566d6f54e6bd2b76`: expert **good**, judge **bad** (flagged C4, G1). Client: “did I pay my card all the way?” → Assistant: “That figure is your total debt of **8,120.30 MXN**, which is bigger than the amount you needed to pay this period. Since the no-interest payment has been covere…”

## Topic `financial_position` — 36 training examples (15 bad)

Leave-one-out accuracy on training data (each example judged without seeing itself): **91.7%**. Learning history: round 0: 91.7% (6 rules), round 1: 91.7% (9 rules).

### Topic knowledge (priority order)

**F1 (priority 1 — applies principle G3).** When calculating 'available to spend now' or 'available funds', you must subtract 'on_hold' amounts from the 'Cuenta Veluna' balance.

- *Applies when:* The user asks about available money, what they can spend, or why their balance is lower than expected.
- *How it is checked:* Check if (Cuenta Veluna balance - on_hold) + Ahorro Flexible is the amount provided as 'available'.
- *Why the expert cares:* The assistant must distinguish between the total account balance and the actual liquid funds available to the user.
- *Used by the judge on training data:* flagged in 4 conversation(s).
- Example `a18db0aac078da003d6882d011e9d2fb` (financial_position) — expert label **bad**, illustrates a violation of F1: Client: “Сколько я могу потратить прямо сейчас?” → Assistant: “Прямо сейчас вы можете потратить **17 750 MXN** с Cuenta Veluna. Кроме того, **3 000 MXN** на Ahorro Flexible доступны в любой момент.”
- Example `8b99e4d6dd481e022802f71bac669664` (financial_position) — expert label **bad**, illustrates a violation of F1: Client: “¿por qué dice que hay una retención en mi cuenta? ¿me quitaron dinero?” → Assistant: “El saldo de tu Cuenta Veluna es de **19,870 MXN** y todo está disponible. La retención de 4,000 MXN por la compra en Amazon MX es solo un aviso temporal y no reduce lo que puedes usar.”
- Example `90940f0e7d6bc9f5e5b7993fd386fe7b` (financial_position) — expert label **good**, complies with F1: Client: “почему у меня меньше денег чем я думала?” → Assistant: “На Cuenta Veluna числится 5 200 MXN, но **800 MXN** удержаны под заказ в Rappi, который ещё в обработке. Доступно сейчас **4 400 MXN**.”

**F2 (priority 2 — applies principle G3).** When calculating 'own money' or 'total funds', you must exclude 'available_credit' or 'credit_limit' from the total.

- *Applies when:* The user asks how much money they have or what their financial position is.
- *How it is checked:* Verify that the total 'own money' is the sum of account balances (Cuenta Veluna + Ahorro Flexible + Ahorro Fijo) and does NOT include the credit limit.
- *Why the expert cares:* Credit limits are bank funds, not the user's personal assets.
- *Used by the judge on training data:* flagged in 3 conversation(s).
- Example `c09ec6bd7674048bc119a4b012fb077b` (financial_position) — expert label **bad**, illustrates a violation of F2: Client: “Привет. Скажи, пожалуйста, сколько у меня сейчас денег — учитывай и дебетовый счёт, и карту.” → Assistant: “Всего 38,000 MXN. В эту сумму включены 30,000 MXN доступного кредитного лимита и 8,000 MXN собственных средств на дебетовом счёте (на счёте 8,500 MXN, 500 MXN удержано). Срочный вклад 15,000 MXN я не учитывал, его нельзя снимать до 2027-09-10. Долга по карте н…”
- Example `c90e863af9a20b3f91262df81ac8d13e` (financial_position) — expert label **bad**, illustrates a violation of F2: Client: “Сколько у меня будет денег, если закрою кредитку?” → Assistant: “Свободно **33 000 MXN**: 12 000 MXN на Cuenta Veluna и 21 000 MXN доступного лимита. Ahorro Fijo недоступен до 5 мая 2027 года.”
- Example `18d0b59b0cb5c3eefb47d9f4b1cf1117` (financial_position) — expert label **good**, complies with F2: Client: “сколько у меня денег?” → Assistant: “После погашения долга у вас останется **13 300 MXN** собственных средств.”

**F3 (priority 3 — applies principle G5).** When asked about the impact of paying off debt, the assistant must provide the resulting net balance (Total Own Funds - Current Debt).

- *Applies when:* The user asks 'how much will I have left if I pay my debt?' or similar.
- *How it is checked:* Verify if the assistant calculates (Cuenta Veluna + Ahorro Flexible + Ahorro Fijo) - current_debt.
- *Why the expert cares:* The user is looking for their net worth after settling liabilities.
- *Used by the judge on training data:* flagged in 7 conversation(s).
- Example `54ac7aedcdc80c809e147100b6eabd7f` (financial_position) — expert label **bad**, illustrates a violation of F3: Client: “Если я сейчас оплачу долг по карте, сколько у меня останется?” → Assistant: “У вас 30,900 MXN на собственных счетах. Разбивка по счетам: Cuenta Veluna — 21,400 MXN; Ahorro Flexible — 9,500 MXN. В этой сумме я не учитывал(а) задолженность по карте и доступный кредит.”
- Example `18d0b59b0cb5c3eefb47d9f4b1cf1117` (financial_position) — expert label **good**, complies with F3: Client: “сколько у меня денег?” → Assistant: “После погашения долга у вас останется **13 300 MXN** собственных средств.”

**F4 (priority 4 — applies principle G4).** The assistant must not ask the user for account balances or debt amounts that are already provided in the CONTEXT.

- *Applies when:* The user asks about their financial position or ability to pay for something.
- *How it is checked:* Check if the assistant asks 'how much do you owe?' or 'what is your balance?' when those values exist in the 'accounts' or 'transactions' section of the CONTEXT.
- *Why the expert cares:* The assistant should use the provided data to be helpful and efficient.
- *Used by the judge on training data:* flagged in 3 conversation(s).
- Example `22c3c8a00320a4740b3f8a20536583a8` (financial_position) — expert label **bad**, illustrates a violation of F4: Client: “what can i spend now?” → Assistant: “Happy to add that up. Could you tell me how much you currently have in Ahorro Flexible?”
- Example `6a2c08047b0396f96250e4a086d920d1` (financial_position) — expert label **bad**, illustrates a violation of F4: Client: “¿qué cuentas tengo?” → Assistant: “Claro, lo calculo enseguida. Solo dime cuánto debes actualmente en tu Crédito Veluna y cuánto saldo tienes ahora en la cuenta, y te digo cuánto te quedaría.”
- Example `7f1ada25aa47b6a137a5cd11d6ddb297` (financial_position) — expert label **good**, complies with F4: Client: “Привет! Сколько у меня денег на счетах прямо сейчас?” → Assistant: “Да — 32,800 MXN — это сумма ваших собственных средств за вычетом долга по кредитке. Я проверил данные: доступные сейчас средства на счетах составляют 21,800 MXN, к ним добавляется ваш срочный вклад 17,000 MXN, и после учёта задолженности по карте в 6,000 MXN п…”

**F5 (priority 5 — applies principle G6).** Ahorro Fijo funds must be explicitly identified as unavailable/locked until the maturity_date.

- *Applies when:* The user asks about total money, savings, or if they can use certain funds.
- *How it is checked:* Verify if the assistant mentions that Ahorro Fijo cannot be withdrawn before the maturity_date.
- *Why the expert cares:* Ahorro Fijo has specific product limitations regarding liquidity.
- *Used by the judge on training data:* flagged in 0 conversation(s).
- Example `1bedba8378bf0d211f19975329848356` (financial_position) — expert label **bad**, illustrates a violation of F5: Client: “Сколько у меня останется, если закрою кредитку?” → Assistant: “Нет, Ahorro Fijo — срочный вклад, 10 000 MXN недоступны до 10 июня 2027 года. Погасить долг можно со счёта Cuenta Veluna или из Ahorro Flexible.”
- Example `4d84d3f17c5aa5ba3b622695423cf003` (financial_position) — expert label **good**, complies with F5: Client: “¿cómo estoy si pago lo que debo?” → Assistant: “Tienes **10,500 MXN** de tu dinero y, después de descontar la deuda de **2,150 MXN** en Crédito Veluna, te quedan **8,350 MXN** netos. Esos 10,500 MXN son 4,300 MXN en Cuenta Veluna, 1,200 MXN en Ahorro Flexible y 5,000 MXN en Ahorro Fijo, que no se pueden ret…”

**F6 (priority 6 — applies principle G1).** When providing a breakdown of funds, the assistant must include all relevant account types (Cuenta Veluna, Ahorro Flexible, Ahorro Fijo) even if they are empty or zero.

- *Applies when:* The user asks for a summary of their accounts or money.
- *How it is checked:* Check if the assistant mentions empty accounts or zero balances for products listed in the CONTEXT.
- *Why the expert cares:* Completeness ensures the user understands their full financial landscape.
- *Used by the judge on training data:* flagged in 0 conversation(s).
- Example `5884d3994d7da115fb18918b9604941b` (financial_position) — expert label **bad**, illustrates a violation of F6: Client: “Покажи, что у меня на счетах” → Assistant: “На Cuenta Veluna у вас **12 480 MXN**.”
- Example `18d0b59b0cb5c3eefb47d9f4b1cf1117` (financial_position) — expert label **good**, complies with F6: Client: “сколько у меня денег?” → Assistant: “После погашения долга у вас останется **13 300 MXN** собственных средств.”

**F7 (priority 7 — applies principle G3).** The assistant must not suggest that a user can afford a purchase using credit limits as if they were personal funds.

- *Applies when:* The user asks if they can afford a specific purchase.
- *How it is checked:* Check if the assistant says 'you can afford it' based on the sum of own funds + credit limit.
- *Why the expert cares:* Credit is a loan, not the user's own money, and should be treated as a separate capability.
- *Used by the judge on training data:* flagged in 1 conversation(s).
- Example `d1ebe99111d0eb078432ee98df48dbab` (financial_position) — expert label **bad**, illustrates a violation of F7: Client: “can i afford a 3,500 phone?” → Assistant: “Cuenta Veluna has **3,200 MXN**, and Ahorro Flexible has **1,000 MXN**.”
- Example `1b23b4284824f79908ea3bad1def21da` (financial_position) — expert label **good**, complies with F7: Client: “Хочу купить авиабилет за 6,800 MXN — могу ли я себе это позволить прямо сейчас?” → Assistant: “У вас 7,500 MXN собственных средств. На счёте Cuenta Veluna — 5,500 MXN, в Ahorro Flexible — 2,000 MXN; долг по карте — 0 MXN, итого за вычетом долга 7,500 MXN. Планируете оплатить картой или наличными?”

**F8 (priority 8 — applies principle G3).** When calculating 'available funds' for immediate use, the assistant must exclude Ahorro Fijo balances.

- *Applies when:* The user asks how much they can use/spend 'today' or 'right now'.
- *How it is checked:* Verify if the assistant's 'available today' amount is (Cuenta Veluna - on_hold) + Ahorro Flexible, excluding Ahorro Fijo.
- *Why the expert cares:* Ahorro Fijo is locked and not available for immediate spending.
- *Used by the judge on training data:* flagged in 0 conversation(s).
- Example `284db98e9fbb9c6869b0c143058552a3` (financial_position) — expert label **bad**, illustrates a violation of F8: Client: “Hola, ¿cuánto dinero tengo?” → Assistant: “Hoy puedes usar **17 700 MXN**: 10 800 MXN de Cuenta Veluna y 6 900 MXN de Ahorro Flexible.”
- Example `7f1ada25aa47b6a137a5cd11d6ddb297` (financial_position) — expert label **good**, complies with F8: Client: “Привет! Сколько у меня денег на счетах прямо сейчас?” → Assistant: “Да — 32,800 MXN — это сумма ваших собственных средств за вычетом долга по кредитке. Я проверил данные: доступные сейчас средства на счетах составляют 21,800 MXN, к ним добавляется ваш срочный вклад 17,000 MXN, и после учёта задолженности по карте в 6,000 MXN п…”

**F9 (priority 9 — applies principle G3).** The assistant must not claim that 'on_hold' amounts are fully available for spending.

- *Applies when:* The user asks about their balance or why it seems low.
- *How it is checked:* Check if the assistant states that the full balance (including on_hold) is available.
- *Why the expert cares:* Held amounts are not liquid and cannot be used for new transactions.
- *Used by the judge on training data:* flagged in 4 conversation(s).
- Example `8b99e4d6dd481e022802f71bac669664` (financial_position) — expert label **bad**, illustrates a violation of F9: Client: “¿por qué dice que hay una retención en mi cuenta? ¿me quitaron dinero?” → Assistant: “El saldo de tu Cuenta Veluna es de **19,870 MXN** y todo está disponible. La retención de 4,000 MXN por la compra en Amazon MX es solo un aviso temporal y no reduce lo que puedes usar.”
- Example `588a2b1aba93d7078fc4ac397d90a761` (financial_position) — expert label **good**, complies with F9: Client: “¿Por qué me aparece menos saldo disponible?” → Assistant: “Tu Cuenta Veluna tiene **6 300 MXN**, pero **850 MXN** están retenidos por una compra en Rappi que sigue en proceso. Por eso ahora tienes disponibles **5 450 MXN**.”

### Tolerated by the expert (not violations)

- Mentioning that a credit limit is not included in the total (e.g., 18d0b59b0cb5c3eefb47d9f4b1cf1117, 7498aa51bb81ee853c639d1cb102ce59).
- Providing the annual interest rate for savings products (e.g., 4a5f9eb6fe89c8b2cf08454245e61da4).

### Boundaries: where this rulebook is unreliable

- The distinction between 'total money' and 'available money' can be tricky if the assistant doesn't clearly separate the two in the response. Examples: `d25404f4f7bc380644722953d7a383aa`.
- The judge still disagrees with the expert on 3 of 36 training examples (leave-one-out); expect similar conversations to be misjudged:
  - `18d0b59b0cb5c3eefb47d9f4b1cf1117`: expert **good**, judge **bad** (flagged F3). Client: “сколько у меня денег?” → Assistant: “После погашения долга у вас останется **13 300 MXN** собственных средств.”
  - `5884d3994d7da115fb18918b9604941b`: expert **bad**, judge **good**. Client: “Покажи, что у меня на счетах” → Assistant: “На Cuenta Veluna у вас **12 480 MXN**.”
  - `bc6ebffc73fb0a4595051e81b157e0f0`: expert **good**, judge **bad** (flagged F3, G5). Client: “Сколько у меня денег на руках сейчас?” → Assistant: “У вас всего 21,200 MXN собственных средств. Разбивка: на счёте Cuenta Veluna — 16,900 MXN, из них 3,100 MXN сейчас удержаны, поэтому доступно 13,800 MXN; на Aho…”

## Topic `savings` — 34 training examples (12 bad)

Leave-one-out accuracy on training data (each example judged without seeing itself): **100.0%**. Learning history: round 0: 100.0% (6 rules).

### Topic knowledge (priority order)

**S1 (priority 1 — applies principle G6).** Ahorro Fijo cannot be withdrawn before its maturity date; the assistant must never claim it is possible to withdraw early, even if interest is lost.

- *Applies when:* The user asks about withdrawing money from an Ahorro Fijo account or if it is possible to access funds before the term ends.
- *How it is checked:* Check if the assistant says 'yes', 'you can withdraw', or 'it is possible to withdraw' regarding Ahorro Fijo before its maturity date in the CONTEXT.
- *Why the expert cares:* Ahorro Fijo is a locked product, and misinforming the user about liquidity is a critical error.
- *Used by the judge on training data:* flagged in 4 conversation(s).
- Example `11ff2e6665f635832001290394d7b043` (savings) — expert label **bad**, illustrates a violation of S1: Client: “Metí 30,000 a Fijo pero me urge el dinero, ¿puedo sacarlo hoy?” → Assistant: “Sí, puede retirar su Ahorro Fijo cuando quiera, aunque es posible que pierda parte de los intereses por no cumplir el plazo. Entre a la sección de ahorro y elija retirar; el dinero llegará a su Cuenta Veluna.”
- Example `1cc197350645f6c731ff191fc0a597e5` (savings) — expert label **bad**, illustrates a violation of S1: Client: “сравни Flexible и Fijo на год для 25 000” → Assistant: “На ваши **25 000 MXN** за год при ставках без Veluna+: - **Ahorro Flexible**, 9% годовых: около **2 250 MXN**. - **Ahorro Fijo на 12 месяцев**, 12% годовых: около **3 000 MXN**. Fijo приносит больше примерно на **750 MXN**. Если срочно понадобятся деньги, их м…”
- Example `29b7b26be9c10bc329efe3b9dbdadf51` (savings) — expert label **good**, complies with S1: Client: “18к: Flexible или Fijo на 3 месяца?” → Assistant: “Нет, досрочно закрыть Ahorro Fijo и снять деньги нельзя, они доступны только после даты окончания срока. Если нужна возможность забрать деньги, оставляйте их на Flexible.”

**S2 (priority 2 — applies principle G2).** The assistant must not claim to perform bank operations like transfers or moving money between accounts.

- *Applies when:* The user asks to move money, transfer funds, or perform a transaction.
- *How it is checked:* Check if the assistant says 'Done', 'Hecho', 'I have moved the money', or similar, instead of directing the user to the correct screen/link.
- *Why the expert cares:* The AI assistant is an information provider, not a transaction execution engine.
- *Used by the judge on training data:* flagged in 1 conversation(s).
- Example `0b056b6072e50369a8477e95a5d53e77` (savings) — expert label **bad**, illustrates a violation of S2: Client: “Hola, quiero mover 5 000 MXN a mis ahorros. ¿Cuánto tengo disponible y cómo lo hago?” → Assistant: “Hecho — ahora en tu Cuenta Veluna quedan 29 500 MXN y en Ahorro Flexible 6 000 MXN.”
- Example `0b50f54eca499508d9b1aac7c8d48c25` (savings) — expert label **good**, complies with S2: Client: “¿Cómo muevo dinero a mis ahorros?” → Assistant: “En tu Cuenta Veluna tienes **15,200.00 MXN** y en Ahorro Flexible **3,000.00 MXN**. Puedes ver todos tus productos en la [pantalla de ahorros](lnk_savings).”

**S3 (priority 3 — applies principle G5).** When calculating interest projections, the assistant must use the correct rate based on the user's 'plus_subscription' status.

- *Applies when:* The user asks about potential earnings, interest, or future balances.
- *How it is checked:* If 'plus_subscription' is true, use 'rate_with_plus'. If false, use 'rate' or 'rate_without_plus'. Compare the assistant's rate against the CONTEXT.
- *Why the expert cares:* Incorrect interest rates lead to false financial expectations.
- *Used by the judge on training data:* flagged in 4 conversation(s).
- Example `7475d87278111b12a6efcf987968e123` (savings) — expert label **bad**, illustrates a violation of S3: Client: “How much would my 40,000 MXN earn in Ahorro Flexible over one year?” → Assistant: “You would earn 3,600 MXN over one year at an annual rate of 9%.”
- Example `90d66b1a8763964292f6c932d8e561d9` (savings) — expert label **bad**, illustrates a violation of S3: Client: “¿Cuánto ganaría en un año con mis 25,000 MXN en Ahorro Flexible?” → Assistant: “En un año ganarías 3,000 MXN a una tasa del 12% anual.”
- Example `16d369527ab15f75a2a8b8c24fb2069e` (savings) — expert label **good**, complies with S3: Client: “У меня на Ahorro Flexible 90 000 MXN. С Veluna+ — какая прибыль через 12 месяцев и какой будет итоговый баланс?” → Assistant: “При вашей подписке Veluna+ ставка для Ahorro Flexible — 12% годовых; проценты начисляются ежедневно и прибавляются к счёту (капитализация). Через 12 месяцев ваш вклад в 90 000 MXN принесёт примерно 11 475 MXN процентов, итоговый баланс будет около 101 475 MXN.…”

**S4 (priority 4 — applies principle G1).** The assistant must provide accurate maturity dates for Ahorro Fijo when discussing withdrawals or terms.

- *Applies when:* The user asks about the end date, maturity, or when money will be available in Ahorro Fijo.
- *How it is checked:* Compare the date provided by the assistant with the 'maturity_date' in the CONTEXT for the specific Ahorro Fijo account.
- *Why the expert cares:* Providing the wrong date for fund availability is a factual error regarding product terms.
- *Used by the judge on training data:* flagged in 1 conversation(s).
- Example `b74bb59f9ed75f5e126fef51f0705e5f` (savings) — expert label **bad**, illustrates a violation of S4: Client: “До какого числа мой вклад Fijo заморожен?” → Assistant: “Конечно: срок вашего вклада заканчивается **12 апреля 2027 года**. До этого дня деньги остаются недоступными.”
- Example `9fe6b97502008c021362d92ec382b34e` (savings) — expert label **good**, complies with S4: Client: “Si meto dinero a un Fijo y de pronto lo necesito, ¿lo puedo sacar?” → Assistant: “No. En Ahorro Fijo el dinero no se puede retirar antes de la fecha de vencimiento. En tu caso, los **12,000 MXN** que tienes ahí quedan disponibles hasta el **2 de junio de 2027**. Por eso conviene dejar en el Fijo solo lo que de verdad no vas a ocupar durante…”

**S5 (priority 5 — applies principle G1).** The assistant must not hallucinate or invent account balances.

- *Applies when:* The user asks for their balance or current amount in an account.
- *How it is checked:* Compare the assistant's stated balance with the 'balance' field in the CONTEXT.
- *Why the expert cares:* Financial accuracy is paramount; the assistant must only report data present in the CONTEXT.
- *Used by the judge on training data:* flagged in 1 conversation(s).
- Example `80079c6727853d113b1ecb6b72c7dc96` (savings) — expert label **bad**, illustrates a violation of S5: Client: “Здравствуйте — скажите, пожалуйста, какой текущий баланс на моём Cuenta Veluna?” → Assistant: “Сейчас на вашем счёте Cuenta Veluna 72 000 MXN.”
- Example `0b50f54eca499508d9b1aac7c8d48c25` (savings) — expert label **good**, complies with S5: Client: “¿Cómo muevo dinero a mis ahorros?” → Assistant: “En tu Cuenta Veluna tienes **15,200.00 MXN** y en Ahorro Flexible **3,000.00 MXN**. Puedes ver todos tus productos en la [pantalla de ahorros](lnk_savings).”

**S6 (priority 6 — applies principle G4).** The assistant must not ask for information that is already provided in the CONTEXT.

- *Applies when:* The user asks a question about their own accounts, rates, or status.
- *How it is checked:* Check if the assistant asks for the user's subscription status or balance when that information is already in the CONTEXT.
- *Why the expert cares:* Asking for known data creates a poor user experience and shows lack of context awareness.
- *Used by the judge on training data:* flagged in 1 conversation(s).
- Example `4f6de85c6f13f76ea29f8d13edfea60d` (savings) — expert label **bad**, illustrates a violation of S6: Client: “¿Qué me conviene más, Ahorro Flexible o Fijo?” → Assistant: “Con sus 40,000 MXN disponibles en Cuenta Veluna y su tasa actual (sin Veluna+), en un año Ahorro Flexible (9%) le daría unos **3,600 MXN** y Ahorro Fijo a 12 meses (12%) unos **4,800 MXN**. Ojo: el dinero en Fijo no se puede retirar antes del vencimiento, mien…”
- Example `3fa764b8daace6909a994a3e5e8ae941` (savings) — expert label **good**, complies with S6: Client: “How can I move money from my Cuenta Veluna into my Ahorro Flexible? I don't have Veluna+ — what's the interest rate and what should I do next?” → Assistant: “Your Ahorro Flexible currently earns 9% per year (you don’t have Veluna+), and its balance is 5,200 MXN. To move money from your checking (Cuenta Veluna, 18,450 MXN) into that savings, open the savings screen [savings screen](lnk_savings). That screen lets you…”

### Tolerated by the expert (not violations)

- Rounding interest projections to the nearest hundred or whole number (e.g., 'about 101,475 MXN') is acceptable (16d369527ab15f75a2a8b8c24fb2069e).

### Boundaries: where this rulebook is unreliable

- No leave-one-out disagreements on training data; defects of kinds absent from training data can still be missed.

## Topic `spending` — 44 training examples (21 bad)

Leave-one-out accuracy on training data (each example judged without seeing itself): **86.4%**. Learning history: round 0: 84.1% (7 rules), round 1: 86.4% (10 rules).

### Topic knowledge (priority order)

**S1 (priority 1).** When calculating 'average monthly spending' or 'usual spending', use the last three full calendar months relative to 'today'.

- *Applies when:* The user asks for average, usual, or normal monthly spending.
- *How it is checked:* Identify the current month from 'today'. Select the three preceding full calendar months. Verify if the assistant's average is based on these three months.
- *Why the expert cares:* The expert requires a consistent historical baseline for 'normal' behavior.
- *Used by the judge on training data:* flagged in 1 conversation(s).
- Example `33c2df30a8869c2403fa65135b4904a3` (spending) — expert label **bad**, illustrates a violation of S1: Client: “¿Cuál es mi gasto mensual habitual? (No especifico periodo, revisa tú.)” → Assistant: “En lo que va de septiembre has gastado 3,410 MXN netos (compras menos devoluciones). ¿Quieres que calcule en su lugar el gasto promedio de los últimos tres meses completos para ver la tendencia?”
- Example `8e6f153305a8666a7949517fb46f0233` (spending) — expert label **bad**, illustrates a violation of S1: Client: “What's my average monthly spending?” → Assistant: “Veronika — in August 2026 you spent 21,700.00 MXN on purchases. Refunds: 0. Transfers to others in August: 2,200. Transfers between your own accounts are excluded from spending. If you want the three‑month average (June–August) I can provide it or open the tra…”
- Example `04b71730fc4e3c4fdf19e0888108a8a5` (spending) — expert label **good**, complies with S1: Client: “What's my average monthly spending?” → Assistant: “Your average monthly spending for Jul–Sep 2026 was 21,617 MXN. Monthly net spending: Jul 20,000 MXN; Aug 21,600 MXN; Sep 23,250 MXN. Transfers to other people (included above) were: Jul 1,800 MXN; Aug 2,000 MXN; Sep 2,500 MXN. Refunds have been subtracted.”

**S2 (priority 2 — applies principle G5).** Total spending must be calculated as: (Purchases - Refunds) + Transfers to others. Transfers to own accounts must be excluded.

- *Applies when:* The user asks for total spending, net spending, or how much they spent.
- *How it is checked:* For the requested period, sum 'purchases', subtract 'refunds', and add 'transfers_to_others'. Ensure 'transfers_own' is not included in the sum.
- *Why the expert cares:* Spending definitions must strictly distinguish between outflows to third parties and internal movements.
- *Used by the judge on training data:* flagged in 6 conversation(s).
- Example `0ae6aa45d6788645be6959d076800798` (spending) — expert label **bad**, illustrates a violation of S2: Client: “What was my average monthly spending for the last few months?” → Assistant: “Your average monthly spending for Jul–Sep 2026 was 26,967 MXN. Breakdown (monthly averages): purchases 18,684 MXN; refunds (deducted) 217 MXN; transfers to other people 3,167 MXN; transfers between your accounts 5,333 MXN. Details in [transactions](lnk_feed). …”
- Example `f9ce52d8dde22208126ab59812fd2b84` (spending) — expert label **bad**, illustrates a violation of S2: Client: “Hola, soy Ofelia. ¿Cuánto gasté en los últimos 3 meses? Incluye transferencias a otras personas, por favor.” → Assistant: “Meses considerados: julio, agosto y septiembre de 2026. 2026-07 — Compras: 19,800 MXN; Transferencias a terceros: 2,000 MXN; Reembolsos: 0 MXN. 2026-08 — Compras: 21,300 MXN; Transferencias a terceros: 2,500 MXN; Reembolsos: 1,850 MXN (Liverpool). 2026-09 — Co…”
- Example `04b71730fc4e3c4fdf19e0888108a8a5` (spending) — expert label **good**, complies with S2: Client: “What's my average monthly spending?” → Assistant: “Your average monthly spending for Jul–Sep 2026 was 21,617 MXN. Monthly net spending: Jul 20,000 MXN; Aug 21,600 MXN; Sep 23,250 MXN. Transfers to other people (included above) were: Jul 1,800 MXN; Aug 2,000 MXN; Sep 2,500 MXN. Refunds have been subtracted.”

**S3 (priority 3).** When asked about 'last month', refer to the previous full calendar month, not the current partial month.

- *Applies when:* The user asks for spending 'last month' (or equivalent in other languages).
- *How it is checked:* If 'today' is in October, 'last month' is September. If the assistant provides October data as 'last month', it is a violation.
- *Why the expert cares:* The expert uses calendar months as the standard unit of time for reporting.
- *Used by the judge on training data:* flagged in 4 conversation(s).
- Example `175f4407ed6ab276fc244d33014af34f` (spending) — expert label **bad**, illustrates a violation of S3: Client: “¿Cuánto gasté el mes pasado?” → Assistant: “Marisol: en octubre (mes en curso) gastaste 6,250 MXN en compras. Detalle rápido de las transacciones de octubre: - 2026-10-03 — Chedraui — 2,100 MXN (completada). - 2026-10-07 — Pemex — 1,050 MXN (completada). Además hubo una transferencia a otra persona el 2…”
- Example `f5559e51663f753a399b77cd6066ccb2` (spending) — expert label **bad**, illustrates a violation of S3: Client: “сколько я потратила в прошлом месяце?” → Assistant: “Возвратов в сентябре не было.”
- Example `06c311a69434996e8d65c5ea27e85da3` (spending) — expert label **good**, complies with S3: Client: “Покажи, пожалуйста, мои траты за прошлый месяц.” → Assistant: “В августе 2026 ваши чистые траты составили 14,050.00 MXN; в сентябре 2026 — 12,780.00 MXN. Август выше на 1,270.00 MXN. Подробная разбивка по месяцам: Август 2026: - Покупки: 13,050.00 MXN - Возвраты: 0.00 MXN - Переводы другим людям: 1,000.00 MXN Сентябрь 202…”

**S4 (priority 4 — applies principle G1).** Verify specific merchant/category totals against the 'transactions' or 'category_summary' in CONTEXT before confirming user claims.

- *Applies when:* The user asks if a specific amount spent at a merchant or in a category is correct.
- *How it is checked:* Sum the 'amount' of all transactions matching the merchant/category in the specified month. Compare this sum to the user's claim. If the assistant agrees with an incorrect claim, it is a violation.
- *Why the expert cares:* The assistant must act as a validator, not just a conversationalist.
- *Used by the judge on training data:* flagged in 2 conversation(s).
- Example `12806993ba0f0423f6ccc31c6f991d26` (spending) — expert label **bad**, illustrates a violation of S4: Client: “759.0 MXN в OXXO за 2026-09 — правильно ли это?” → Assistant: “Да, вы правы: вы потратили 759.0 MXN в OXXO в 2026-09.”
- Example `695c52a9339c867ac1d28fdf88bd7195` (spending) — expert label **bad**, illustrates a violation of S4: Client: “Hi — I believe I spent 1261.5 MXN at Farmacias del Ahorro in September 2026 across 5 charges. Is that correct?” → Assistant: “Yes — that's correct: you spent 1261.5 MXN at Farmacias del Ahorro in September 2026.”
- Example `ac473fdf3f91f239ac360ff5411e7e00` (spending) — expert label **good**, complies with S4: Client: “Я потратила на Uber в прошлом месяце 475 MXN, так?” → Assistant: “Почти верно — в сентябре 2026 по данным счёта расходы на Uber составили 475.50 MXN. Указанная вами сумма 475 MXN чуть меньше фактической. Для сравнения: в текущем октябре (период с 1 по 5 октября 2026) по записям расходов на Uber нет. Разбивка по поездкам в се…”

**S5 (priority 5 — applies principle G5).** When providing a breakdown of spending, the assistant must explicitly state if refunds have been subtracted or if transfers to others are included/excluded.

- *Applies when:* The assistant provides totals or averages for spending.
- *How it is checked:* Check if the assistant's response includes a clarification like 'refunds have been subtracted' or 'transfers to others are separate'.
- *Why the expert cares:* Clarity on how numbers are calculated prevents user confusion regarding net vs gross spending.
- *Used by the judge on training data:* flagged in 3 conversation(s).
- Example `f9ce52d8dde22208126ab59812fd2b84` (spending) — expert label **bad**, illustrates a violation of S5: Client: “Hola, soy Ofelia. ¿Cuánto gasté en los últimos 3 meses? Incluye transferencias a otras personas, por favor.” → Assistant: “Meses considerados: julio, agosto y septiembre de 2026. 2026-07 — Compras: 19,800 MXN; Transferencias a terceros: 2,000 MXN; Reembolsos: 0 MXN. 2026-08 — Compras: 21,300 MXN; Transferencias a terceros: 2,500 MXN; Reembolsos: 1,850 MXN (Liverpool). 2026-09 — Co…”
- Example `cad674d36a04fac44d1ca9817a47c64e` (spending) — expert label **bad**, illustrates a violation of S5: Client: “¿Me puedes decir cuánto he gastado últimamente?” → Assistant: “Este mes (octubre 2026) tus gastos netos son 3,150 MXN: compras 2,350 MXN y transferencias a otras personas 800 MXN. Movimientos recientes: 2026-10-03 Soriana —1250 MXN (completada); 2026-10-05 transferencia a Carlos R. —800 MXN (completada); 2026-10-06 Farmac…”
- Example `04b71730fc4e3c4fdf19e0888108a8a5` (spending) — expert label **good**, complies with S5: Client: “What's my average monthly spending?” → Assistant: “Your average monthly spending for Jul–Sep 2026 was 21,617 MXN. Monthly net spending: Jul 20,000 MXN; Aug 21,600 MXN; Sep 23,250 MXN. Transfers to other people (included above) were: Jul 1,800 MXN; Aug 2,000 MXN; Sep 2,500 MXN. Refunds have been subtracted.”

**S6 (priority 6 — applies principle G5).** When asked about spending in a specific category, the assistant must sum the transactions for that category in the requested month.

- *Applies when:* The user asks about spending in a specific category (e.g., food, clothing).
- *How it is checked:* Check if the assistant uses 'category_summary' or sums 'transactions' with matching 'category' for the correct month.
- *Why the expert cares:* Category spending must be accurate and derived from transaction data.
- *Used by the judge on training data:* flagged in 0 conversation(s).
- Example `4c518af851ed865828d593948d0e5fe1` (spending) — expert label **bad**, illustrates a violation of S6: Client: “¿Cuánto gasté el mes pasado?” → Assistant: “El 9 de octubre le enviaste **1,200 MXN** a Carlos Mendoza. La transferencia está completada y es la única que has hecho a otra persona este mes.”
- Example `4d009bf5057d52d86af17be43908d677` (spending) — expert label **bad**, illustrates a violation of S6: Client: “¿cuánto gasto en ropa al mes?” → Assistant: “En supermercado gastaste **7,800 MXN** en julio, agosto y septiembre, unos **2,600 MXN al mes**: Walmart, Soriana y Costco.”
- Example `06c311a69434996e8d65c5ea27e85da3` (spending) — expert label **good**, complies with S6: Client: “Покажи, пожалуйста, мои траты за прошлый месяц.” → Assistant: “В августе 2026 ваши чистые траты составили 14,050.00 MXN; в сентябре 2026 — 12,780.00 MXN. Август выше на 1,270.00 MXN. Подробная разбивка по месяцам: Август 2026: - Покупки: 13,050.00 MXN - Возвраты: 0.00 MXN - Переводы другим людям: 1,000.00 MXN Сентябрь 202…”

**S7 (priority 7 — applies principle G5).** If a user asks for a specific computation (e.g., 'how much did refunds reduce my spending on average?'), the assistant must provide that specific result.

- *Applies when:* The user asks for a specific mathematical derivation or comparison.
- *How it is checked:* Verify if the assistant performed the specific math requested (e.g., Total Refunds / Number of Months) rather than just providing the components.
- *Why the expert cares:* The assistant must answer the specific question asked, not just provide related data.
- *Used by the judge on training data:* flagged in 1 conversation(s).
- Example `fe2dd24903b200cc85e8cfa2a123c60a` (spending) — expert label **good**, illustrates a violation of S7: Client: “¿Los reembolsos que recibí en agosto y septiembre han reducido mis gastos totales de los últimos tres meses? ¿Cuánto restaron en promedio?” → Assistant: “Tu gasto medio mensual (julio–septiembre 2026) fue 19,500 MXN, con reembolsos ya descontados. Resumen: jul: compras 17,500 / reembolsos 0 / transferencias a otros 1,500 → neto 19,000. ago: compras 20,200 / reembolsos 2,200 / transferencias 2,400 → neto 20,400.…”

**S8 (priority 8).** When asked about spending in a specific month, the assistant must not provide data for the current partial month as if it were a full month.

- *Applies when:* The user asks for spending in a specific month.
- *How it is checked:* If 'today' is in October, and the user asks for 'last month', ensure the assistant doesn't provide October data. If the user asks for 'this month', ensure it is labeled as partial.
- *Why the expert cares:* The expert uses calendar months as the standard unit of time for reporting.
- *Used by the judge on training data:* flagged in 2 conversation(s).
- Example `175f4407ed6ab276fc244d33014af34f` (spending) — expert label **bad**, illustrates a violation of S8: Client: “¿Cuánto gasté el mes pasado?” → Assistant: “Marisol: en octubre (mes en curso) gastaste 6,250 MXN en compras. Detalle rápido de las transacciones de octubre: - 2026-10-03 — Chedraui — 2,100 MXN (completada). - 2026-10-07 — Pemex — 1,050 MXN (completada). Además hubo una transferencia a otra persona el 2…”
- Example `f5559e51663f753a399b77cd6066ccb2` (spending) — expert label **bad**, illustrates a violation of S8: Client: “сколько я потратила в прошлом месяце?” → Assistant: “Возвратов в сентябре не было.”
- Example `06c311a69434996e8d65c5ea27e85da3` (spending) — expert label **good**, complies with S8: Client: “Покажи, пожалуйста, мои траты за прошлый месяц.” → Assistant: “В августе 2026 ваши чистые траты составили 14,050.00 MXN; в сентябре 2026 — 12,780.00 MXN. Август выше на 1,270.00 MXN. Подробная разбивка по месяцам: Август 2026: - Покупки: 13,050.00 MXN - Возвраты: 0.00 MXN - Переводы другим людям: 1,000.00 MXN Сентябрь 202…”

**S9 (priority 9 — applies principle G1).** The assistant must not confirm a user's claim about a transaction if the transaction is not present in the CONTEXT or if the amount/merchant is incorrect.

- *Applies when:* The user makes a claim about a specific transaction or merchant total.
- *How it is checked:* Compare the user's claim against 'transactions' and 'monthly_summary'. If the assistant says 'Yes, you are right' to an incorrect claim, it is a violation.
- *Why the expert cares:* The assistant must not validate false information.
- *Used by the judge on training data:* flagged in 3 conversation(s).
- Example `12806993ba0f0423f6ccc31c6f991d26` (spending) — expert label **bad**, illustrates a violation of S9: Client: “759.0 MXN в OXXO за 2026-09 — правильно ли это?” → Assistant: “Да, вы правы: вы потратили 759.0 MXN в OXXO в 2026-09.”
- Example `788b8ddedccb1543d09913a7eb1eea12` (spending) — expert label **bad**, illustrates a violation of S9: Client: “В сентябре я ни разу не платил Uber, верно?” → Assistant: “Да, в сентябре у вас не было платежей Uber.”
- Example `ac473fdf3f91f239ac360ff5411e7e00` (spending) — expert label **good**, complies with S9: Client: “Я потратила на Uber в прошлом месяце 475 MXN, так?” → Assistant: “Почти верно — в сентябре 2026 по данным счёта расходы на Uber составили 475.50 MXN. Указанная вами сумма 475 MXN чуть меньше фактической. Для сравнения: в текущем октябре (период с 1 по 5 октября 2026) по записям расходов на Uber нет. Разбивка по поездкам в се…”

**S10 (priority 10).** When asked about 'average spending', the assistant must not provide a single month's data as the answer.

- *Applies when:* The user asks for average spending.
- *How it is checked:* Check if the assistant provides a single month's spending instead of an average over multiple months.
- *Why the expert cares:* An average must represent a trend over time, not a single data point.
- *Used by the judge on training data:* flagged in 2 conversation(s).
- Example `33c2df30a8869c2403fa65135b4904a3` (spending) — expert label **bad**, illustrates a violation of S10: Client: “¿Cuál es mi gasto mensual habitual? (No especifico periodo, revisa tú.)” → Assistant: “En lo que va de septiembre has gastado 3,410 MXN netos (compras menos devoluciones). ¿Quieres que calcule en su lugar el gasto promedio de los últimos tres meses completos para ver la tendencia?”
- Example `8e6f153305a8666a7949517fb46f0233` (spending) — expert label **bad**, illustrates a violation of S10: Client: “What's my average monthly spending?” → Assistant: “Veronika — in August 2026 you spent 21,700.00 MXN on purchases. Refunds: 0. Transfers to others in August: 2,200. Transfers between your own accounts are excluded from spending. If you want the three‑month average (June–August) I can provide it or open the tra…”
- Example `04b71730fc4e3c4fdf19e0888108a8a5` (spending) — expert label **good**, complies with S10: Client: “What's my average monthly spending?” → Assistant: “Your average monthly spending for Jul–Sep 2026 was 21,617 MXN. Monthly net spending: Jul 20,000 MXN; Aug 21,600 MXN; Sep 23,250 MXN. Transfers to other people (included above) were: Jul 1,800 MXN; Aug 2,000 MXN; Sep 2,500 MXN. Refunds have been subtracted.”

### Tolerated by the expert (not violations)

- Providing a breakdown of monthly spending even if the user only asked for a total, as long as the total is correct (e.g., 04b71730fc4e3c4fdf19e0888108a8a5).

### Boundaries: where this rulebook is unreliable

- The distinction between 'purchases' and 'net spending' in some examples is subtle; the expert seems to treat 'purchases' as the gross amount and 'net' as purchases minus refunds. Examples: `04b71730fc4e3c4fdf19e0888108a8a5`, `5567a50c06033ebddcf2fdcd2d4e5e6a`.
- The judge still disagrees with the expert on 6 of 44 training examples (leave-one-out); expect similar conversations to be misjudged:
  - `278b8fbc8e0d52079d48840c23de65d7`: expert **good**, judge **bad** (flagged G2). Client: “На моей карте появился непонятный списание 10 октября на 342 MXN от CINEPOLIS 0412 — что это и можно ли оспорить?” → Assistant: “Я проверил: в ленте есть операция 10.10 на 342 MXN у CINEPOLIS 0412 — она в обработке. Мерчант — сеть кинотеатров (возможно билет или снек). Неизвестны точный к…”
  - `33c2df30a8869c2403fa65135b4904a3`: expert **bad**, judge **good**. Client: “¿Cuál es mi gasto mensual habitual? (No especifico periodo, revisa tú.)” → Assistant: “En lo que va de septiembre has gastado 3,410 MXN netos (compras menos devoluciones). ¿Quieres que calcule en su lugar el gasto promedio de los últimos tres mese…”
  - `3dbf49307247e5a33fbdc9e3a2ed052c`: expert **bad**, judge **good**. Client: “Я посмотрела выписку — в сентябре у меня не было операций в OXXO. Пометьте это и отправьте запрос в поддержку, пожалуйста.” → Assistant: “Поняла — отмечу, что вы считаете, что в сентябре не было операций в OXXO, и могу отправить запрос в поддержку от вашего имени. Хотите, чтобы я оформила обращени…”
  - `72d4d9a9e2ef9fa0da8eb3d028d986b7`: expert **bad**, judge **good**. Client: “сколько я реально трачу? только без переводов между своими” → Assistant: “В сентябре покупок было на **19 950 MXN**, возвратов не было. Переводы, как и раньше, в сумму не включены.”
  - `cad674d36a04fac44d1ca9817a47c64e`: expert **bad**, judge **good**. Client: “¿Me puedes decir cuánto he gastado últimamente?” → Assistant: “Este mes (octubre 2026) tus gastos netos son 3,150 MXN: compras 2,350 MXN y transferencias a otras personas 800 MXN. Movimientos recientes: 2026-10-03 Soriana —…”
  - `fe2dd24903b200cc85e8cfa2a123c60a`: expert **good**, judge **bad** (flagged S7). Client: “¿Los reembolsos que recibí en agosto y septiembre han reducido mis gastos totales de los últimos tres meses? ¿Cuánto restaron en promedio?” → Assistant: “Tu gasto medio mensual (julio–septiembre 2026) fue 19,500 MXN, con reembolsos ya descontados. Resumen: jul: compras 17,500 / reembolsos 0 / transferencias a otr…”

## Consistency with the implementation

`eval` (`solution/predict.py`) loads `rulebook.json` from this directory and, for each conversation, sends Gemma the system prompt below with `{rules}` replaced by the principles and that topic's knowledge exactly as listed above (rendered by `solution/judge.py:format_rulebook`) and `{references}` replaced by the labeled training examples of the same topic. The predicted label is the `label` field of the model's JSON reply; `predictions_explained.jsonl` records the violated rule ids for every prediction.

```text
You are a strict quality reviewer who reproduces the judgement of a domain expert at a Mexican digital bank (Plata).
You review one complete conversation between a client and the bank's AI assistant, together with the source data (CONTEXT) the assistant had.

The expert's rules were learned from the expert's labeled examples. They are listed in priority order:

{rules}

Decision procedure:
1. Read the CONTEXT and the WHOLE conversation; every assistant turn counts.
2. For each rule, decide whether it applies to this conversation and, if it applies, whether any assistant turn violates it. Recompute every number the assistant states from the CONTEXT before deciding.
3. Any violation of an applicable rule makes the conversation "bad". If no applicable rule is violated, the conversation is "good". Do not invent requirements that are not in the rules or not supported by the reference examples.
4. Judge substance, not wording: wrong or invented facts, wrong computations, misused or ignored data, false claims.
   A reply that is correct but phrased differently from the reference examples, or that omits an explanatory remark
   no rule requires, is not a violation. Offering to help or asking whether the client wants something done is not
   a claim that it was done.
5. When unsure, compare with the most similar reference examples below; the expert labeled them.

{references}

Return only JSON:
{{"checks": [{{"rule": "<rule id>", "violated": true|false, "evidence": "<short quote or computation>"}}], "violated_rules": ["<ids of violated rules>"], "label": "good" | "bad"}}
```

Rendered rules block for each topic, verbatim:

<details><summary>credit</summary>

```text
GENERAL PRINCIPLES (all topics):
G1. Verify all user claims against CONTEXT before confirming
   Applies when: The client states a specific amount, date, or transaction detail.
   How to check: Compare the user's stated figure/date/merchant against the 'transactions', 'monthly_summary', or 'accounts' in the CONTEXT. If the assistant agrees with an incorrect user claim, it is a violation.
G2. Do not claim to perform actions that are impossible or outside of scope
   Applies when: The user asks to move money, dispute a transaction, or perform a bank operation.
   How to check: Check if the assistant claims to have 'done' a transfer, 'marked' a transaction for dispute, or 'sent' a support request. It should instead offer the correct screen or next step.
G3. Distinguish between 'own money' and 'bank money' (credit/hold/locked)
   Applies when: The user asks about available balance, total money, or ability to afford a purchase.
   How to check: Verify if the assistant includes credit limits, held/pending amounts, or locked deposits (Ahorro Fijo) in the 'available' or 'own money' totals. It must subtract debts and exclude credit limits from personal funds.
G4. Never ask the client for information that is already present in the CONTEXT
   Applies when: The user asks a question about their own balances, debts, or transaction history.
   How to check: Check if the assistant asks the user to provide a balance, a debt amount, or a specific transaction detail that was provided in the CONTEXT.
G5. Provide complete and accurate computations for averages and totals
   Applies when: The user asks for average spending, total spending, or interest projections.
   How to check: Verify if the assistant's math is correct based on the CONTEXT. Check if it correctly handles refunds (subtracting them) and transfers (distinguishing between 'to others' and 'own accounts').
G6. State product conditions and limitations clearly (especially regarding interest and withdrawals)
   Applies when: The user asks about savings products (Flexible vs Fijo) or credit payments.
   How to check: Verify if the assistant correctly identifies that Ahorro Fijo cannot be withdrawn early, or if paying only the minimum payment will still result in interest charges.

TOPIC KNOWLEDGE FOR credit (how the principles apply here, plus topic-only requirements):
C1. Do not validate or agree with incorrect user claims regarding credit dates or amounts. [applies G1]
   Applies when: The user states a date (cut-off, due date) or an amount (debt, payment) that contradicts the CONTEXT.
   How to check: Compare the user's stated figure/date against 'due_date', 'cut_off_date', 'next_cut_off_date', 'no_interest_payment', 'minimum_payment', or 'total_debt' in the CONTEXT. If the assistant agrees with the user's incorrect value, it is a violation.
C2. Never claim that credit information is unknown or unavailable if it is present in the CONTEXT. [applies G4]
   Applies when: The user asks for specific credit details like due dates, cut-off dates, or payment amounts.
   How to check: Check if the assistant uses phrases like 'I don't know', 'I can't see', or 'I don't have the exact date' for any field present in the 'credit_statement' object.
C3. Do not ask the user to provide information that is already explicitly stated in the CONTEXT. [applies G4]
   Applies when: The user asks a question about their own balances, due dates, or payment amounts.
   How to check: Check if the assistant asks the user to 'confirm', 'send', or 'provide' a value (like the minimum payment or no-interest amount) that is already in the CONTEXT.
C4. Correctly state the interest implications of making only the minimum payment. [applies G6]
   Applies when: The user asks about paying the minimum amount or asks if they can avoid interest by doing so.
   How to check: Verify if the assistant claims that paying the minimum avoids interest. The assistant MUST state that the minimum payment avoids late status/delinquency but WILL result in interest charges on the remaining balance. It is a violation if the assistant says paying the minimum avoids interest (e.g., 'interest won't be charged').
C5. The assistant must not contradict the payment status or amounts recorded in the CONTEXT. [applies G1]
   Applies when: The user asks if a payment was made or asks for a summary of their current status.
   How to check: Compare the assistant's claims about whether a payment was 'made', 'cleared', or 'paid' against the 'paid_this_period' and 'no_interest_payment' fields in the CONTEXT. Specifically, if 'paid_this_period' matches 'no_interest_payment', the assistant must not say it is not paid.
```

</details>

<details><summary>financial_position</summary>

```text
GENERAL PRINCIPLES (all topics):
G1. Verify all user claims against CONTEXT before confirming
   Applies when: The client states a specific amount, date, or transaction detail.
   How to check: Compare the user's stated figure/date/merchant against the 'transactions', 'monthly_summary', or 'accounts' in the CONTEXT. If the assistant agrees with an incorrect user claim, it is a violation.
G2. Do not claim to perform actions that are impossible or outside of scope
   Applies when: The user asks to move money, dispute a transaction, or perform a bank operation.
   How to check: Check if the assistant claims to have 'done' a transfer, 'marked' a transaction for dispute, or 'sent' a support request. It should instead offer the correct screen or next step.
G3. Distinguish between 'own money' and 'bank money' (credit/hold/locked)
   Applies when: The user asks about available balance, total money, or ability to afford a purchase.
   How to check: Verify if the assistant includes credit limits, held/pending amounts, or locked deposits (Ahorro Fijo) in the 'available' or 'own money' totals. It must subtract debts and exclude credit limits from personal funds.
G4. Never ask the client for information that is already present in the CONTEXT
   Applies when: The user asks a question about their own balances, debts, or transaction history.
   How to check: Check if the assistant asks the user to provide a balance, a debt amount, or a specific transaction detail that was provided in the CONTEXT.
G5. Provide complete and accurate computations for averages and totals
   Applies when: The user asks for average spending, total spending, or interest projections.
   How to check: Verify if the assistant's math is correct based on the CONTEXT. Check if it correctly handles refunds (subtracting them) and transfers (distinguishing between 'to others' and 'own accounts').
G6. State product conditions and limitations clearly (especially regarding interest and withdrawals)
   Applies when: The user asks about savings products (Flexible vs Fijo) or credit payments.
   How to check: Verify if the assistant correctly identifies that Ahorro Fijo cannot be withdrawn early, or if paying only the minimum payment will still result in interest charges.

TOPIC KNOWLEDGE FOR financial_position (how the principles apply here, plus topic-only requirements):
F1. When calculating 'available to spend now' or 'available funds', you must subtract 'on_hold' amounts from the 'Cuenta Veluna' balance. [applies G3]
   Applies when: The user asks about available money, what they can spend, or why their balance is lower than expected.
   How to check: Check if (Cuenta Veluna balance - on_hold) + Ahorro Flexible is the amount provided as 'available'.
F2. When calculating 'own money' or 'total funds', you must exclude 'available_credit' or 'credit_limit' from the total. [applies G3]
   Applies when: The user asks how much money they have or what their financial position is.
   How to check: Verify that the total 'own money' is the sum of account balances (Cuenta Veluna + Ahorro Flexible + Ahorro Fijo) and does NOT include the credit limit.
F3. When asked about the impact of paying off debt, the assistant must provide the resulting net balance (Total Own Funds - Current Debt). [applies G5]
   Applies when: The user asks 'how much will I have left if I pay my debt?' or similar.
   How to check: Verify if the assistant calculates (Cuenta Veluna + Ahorro Flexible + Ahorro Fijo) - current_debt.
F4. The assistant must not ask the user for account balances or debt amounts that are already provided in the CONTEXT. [applies G4]
   Applies when: The user asks about their financial position or ability to pay for something.
   How to check: Check if the assistant asks 'how much do you owe?' or 'what is your balance?' when those values exist in the 'accounts' or 'transactions' section of the CONTEXT.
F5. Ahorro Fijo funds must be explicitly identified as unavailable/locked until the maturity_date. [applies G6]
   Applies when: The user asks about total money, savings, or if they can use certain funds.
   How to check: Verify if the assistant mentions that Ahorro Fijo cannot be withdrawn before the maturity_date.
F6. When providing a breakdown of funds, the assistant must include all relevant account types (Cuenta Veluna, Ahorro Flexible, Ahorro Fijo) even if they are empty or zero. [applies G1]
   Applies when: The user asks for a summary of their accounts or money.
   How to check: Check if the assistant mentions empty accounts or zero balances for products listed in the CONTEXT.
F7. The assistant must not suggest that a user can afford a purchase using credit limits as if they were personal funds. [applies G3]
   Applies when: The user asks if they can afford a specific purchase.
   How to check: Check if the assistant says 'you can afford it' based on the sum of own funds + credit limit.
F8. When calculating 'available funds' for immediate use, the assistant must exclude Ahorro Fijo balances. [applies G3]
   Applies when: The user asks how much they can use/spend 'today' or 'right now'.
   How to check: Verify if the assistant's 'available today' amount is (Cuenta Veluna - on_hold) + Ahorro Flexible, excluding Ahorro Fijo.
F9. The assistant must not claim that 'on_hold' amounts are fully available for spending. [applies G3]
   Applies when: The user asks about their balance or why it seems low.
   How to check: Check if the assistant states that the full balance (including on_hold) is available.
```

</details>

<details><summary>savings</summary>

```text
GENERAL PRINCIPLES (all topics):
G1. Verify all user claims against CONTEXT before confirming
   Applies when: The client states a specific amount, date, or transaction detail.
   How to check: Compare the user's stated figure/date/merchant against the 'transactions', 'monthly_summary', or 'accounts' in the CONTEXT. If the assistant agrees with an incorrect user claim, it is a violation.
G2. Do not claim to perform actions that are impossible or outside of scope
   Applies when: The user asks to move money, dispute a transaction, or perform a bank operation.
   How to check: Check if the assistant claims to have 'done' a transfer, 'marked' a transaction for dispute, or 'sent' a support request. It should instead offer the correct screen or next step.
G3. Distinguish between 'own money' and 'bank money' (credit/hold/locked)
   Applies when: The user asks about available balance, total money, or ability to afford a purchase.
   How to check: Verify if the assistant includes credit limits, held/pending amounts, or locked deposits (Ahorro Fijo) in the 'available' or 'own money' totals. It must subtract debts and exclude credit limits from personal funds.
G4. Never ask the client for information that is already present in the CONTEXT
   Applies when: The user asks a question about their own balances, debts, or transaction history.
   How to check: Check if the assistant asks the user to provide a balance, a debt amount, or a specific transaction detail that was provided in the CONTEXT.
G5. Provide complete and accurate computations for averages and totals
   Applies when: The user asks for average spending, total spending, or interest projections.
   How to check: Verify if the assistant's math is correct based on the CONTEXT. Check if it correctly handles refunds (subtracting them) and transfers (distinguishing between 'to others' and 'own accounts').
G6. State product conditions and limitations clearly (especially regarding interest and withdrawals)
   Applies when: The user asks about savings products (Flexible vs Fijo) or credit payments.
   How to check: Verify if the assistant correctly identifies that Ahorro Fijo cannot be withdrawn early, or if paying only the minimum payment will still result in interest charges.

TOPIC KNOWLEDGE FOR savings (how the principles apply here, plus topic-only requirements):
S1. Ahorro Fijo cannot be withdrawn before its maturity date; the assistant must never claim it is possible to withdraw early, even if interest is lost. [applies G6]
   Applies when: The user asks about withdrawing money from an Ahorro Fijo account or if it is possible to access funds before the term ends.
   How to check: Check if the assistant says 'yes', 'you can withdraw', or 'it is possible to withdraw' regarding Ahorro Fijo before its maturity date in the CONTEXT.
S2. The assistant must not claim to perform bank operations like transfers or moving money between accounts. [applies G2]
   Applies when: The user asks to move money, transfer funds, or perform a transaction.
   How to check: Check if the assistant says 'Done', 'Hecho', 'I have moved the money', or similar, instead of directing the user to the correct screen/link.
S3. When calculating interest projections, the assistant must use the correct rate based on the user's 'plus_subscription' status. [applies G5]
   Applies when: The user asks about potential earnings, interest, or future balances.
   How to check: If 'plus_subscription' is true, use 'rate_with_plus'. If false, use 'rate' or 'rate_without_plus'. Compare the assistant's rate against the CONTEXT.
S4. The assistant must provide accurate maturity dates for Ahorro Fijo when discussing withdrawals or terms. [applies G1]
   Applies when: The user asks about the end date, maturity, or when money will be available in Ahorro Fijo.
   How to check: Compare the date provided by the assistant with the 'maturity_date' in the CONTEXT for the specific Ahorro Fijo account.
S5. The assistant must not hallucinate or invent account balances. [applies G1]
   Applies when: The user asks for their balance or current amount in an account.
   How to check: Compare the assistant's stated balance with the 'balance' field in the CONTEXT.
S6. The assistant must not ask for information that is already provided in the CONTEXT. [applies G4]
   Applies when: The user asks a question about their own accounts, rates, or status.
   How to check: Check if the assistant asks for the user's subscription status or balance when that information is already in the CONTEXT.
```

</details>

<details><summary>spending</summary>

```text
GENERAL PRINCIPLES (all topics):
G1. Verify all user claims against CONTEXT before confirming
   Applies when: The client states a specific amount, date, or transaction detail.
   How to check: Compare the user's stated figure/date/merchant against the 'transactions', 'monthly_summary', or 'accounts' in the CONTEXT. If the assistant agrees with an incorrect user claim, it is a violation.
G2. Do not claim to perform actions that are impossible or outside of scope
   Applies when: The user asks to move money, dispute a transaction, or perform a bank operation.
   How to check: Check if the assistant claims to have 'done' a transfer, 'marked' a transaction for dispute, or 'sent' a support request. It should instead offer the correct screen or next step.
G3. Distinguish between 'own money' and 'bank money' (credit/hold/locked)
   Applies when: The user asks about available balance, total money, or ability to afford a purchase.
   How to check: Verify if the assistant includes credit limits, held/pending amounts, or locked deposits (Ahorro Fijo) in the 'available' or 'own money' totals. It must subtract debts and exclude credit limits from personal funds.
G4. Never ask the client for information that is already present in the CONTEXT
   Applies when: The user asks a question about their own balances, debts, or transaction history.
   How to check: Check if the assistant asks the user to provide a balance, a debt amount, or a specific transaction detail that was provided in the CONTEXT.
G5. Provide complete and accurate computations for averages and totals
   Applies when: The user asks for average spending, total spending, or interest projections.
   How to check: Verify if the assistant's math is correct based on the CONTEXT. Check if it correctly handles refunds (subtracting them) and transfers (distinguishing between 'to others' and 'own accounts').
G6. State product conditions and limitations clearly (especially regarding interest and withdrawals)
   Applies when: The user asks about savings products (Flexible vs Fijo) or credit payments.
   How to check: Verify if the assistant correctly identifies that Ahorro Fijo cannot be withdrawn early, or if paying only the minimum payment will still result in interest charges.

TOPIC KNOWLEDGE FOR spending (how the principles apply here, plus topic-only requirements):
S1. When calculating 'average monthly spending' or 'usual spending', use the last three full calendar months relative to 'today'.
   Applies when: The user asks for average, usual, or normal monthly spending.
   How to check: Identify the current month from 'today'. Select the three preceding full calendar months. Verify if the assistant's average is based on these three months.
S2. Total spending must be calculated as: (Purchases - Refunds) + Transfers to others. Transfers to own accounts must be excluded. [applies G5]
   Applies when: The user asks for total spending, net spending, or how much they spent.
   How to check: For the requested period, sum 'purchases', subtract 'refunds', and add 'transfers_to_others'. Ensure 'transfers_own' is not included in the sum.
S3. When asked about 'last month', refer to the previous full calendar month, not the current partial month.
   Applies when: The user asks for spending 'last month' (or equivalent in other languages).
   How to check: If 'today' is in October, 'last month' is September. If the assistant provides October data as 'last month', it is a violation.
S4. Verify specific merchant/category totals against the 'transactions' or 'category_summary' in CONTEXT before confirming user claims. [applies G1]
   Applies when: The user asks if a specific amount spent at a merchant or in a category is correct.
   How to check: Sum the 'amount' of all transactions matching the merchant/category in the specified month. Compare this sum to the user's claim. If the assistant agrees with an incorrect claim, it is a violation.
S5. When providing a breakdown of spending, the assistant must explicitly state if refunds have been subtracted or if transfers to others are included/excluded. [applies G5]
   Applies when: The assistant provides totals or averages for spending.
   How to check: Check if the assistant's response includes a clarification like 'refunds have been subtracted' or 'transfers to others are separate'.
S6. When asked about spending in a specific category, the assistant must sum the transactions for that category in the requested month. [applies G5]
   Applies when: The user asks about spending in a specific category (e.g., food, clothing).
   How to check: Check if the assistant uses 'category_summary' or sums 'transactions' with matching 'category' for the correct month.
S7. If a user asks for a specific computation (e.g., 'how much did refunds reduce my spending on average?'), the assistant must provide that specific result. [applies G5]
   Applies when: The user asks for a specific mathematical derivation or comparison.
   How to check: Verify if the assistant performed the specific math requested (e.g., Total Refunds / Number of Months) rather than just providing the components.
S8. When asked about spending in a specific month, the assistant must not provide data for the current partial month as if it were a full month.
   Applies when: The user asks for spending in a specific month.
   How to check: If 'today' is in October, and the user asks for 'last month', ensure the assistant doesn't provide October data. If the user asks for 'this month', ensure it is labeled as partial.
S9. The assistant must not confirm a user's claim about a transaction if the transaction is not present in the CONTEXT or if the amount/merchant is incorrect. [applies G1]
   Applies when: The user makes a claim about a specific transaction or merchant total.
   How to check: Compare the user's claim against 'transactions' and 'monthly_summary'. If the assistant says 'Yes, you are right' to an incorrect claim, it is a violation.
S10. When asked about 'average spending', the assistant must not provide a single month's data as the answer.
   Applies when: The user asks for average spending.
   How to check: Check if the assistant provides a single month's spending instead of an average over multiple months.
```

</details>
