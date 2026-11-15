# دليل تشغيل ورفع Earth Under Decision — بدون VS Code

## الطريقة الأولى: تشغيل الموقع على جهازك

### المتطلبات
- Windows 10/11.
- Docker Desktop مثبت ويعمل.
- اتصال إنترنت لأول Build فقط لتنزيل Docker images والحزم البرمجية.

### التشغيل
1. فك ضغط `Earth_Under_Decision_Full_Stack_2026.zip` في مجلد ثابت.
2. افتح Docker Desktop وانتظر رسالة أن Docker Engine يعمل.
3. ادخل مجلد `earth-under-decision`.
4. اضغط مرتين `START_EARTH_UNDER_DECISION.bat`.
5. انتظر حتى تظهر رسالة فتح الموقع. سيبدأ Docker قاعدة PostGIS، ويطبّق migrations، ثم يشغّل FastAPI الذي يقدم ملفات React المبنية.
6. افتح `http://localhost:8000` إذا لم يفتح تلقائيًا.
7. وثائق API في `http://localhost:8000/docs`.
8. الحالة الصحية في `http://localhost:8000/health`، وجاهزية DB/PostGIS في `http://localhost:8000/ready`.

### الإيقاف والسجلات
- اضغط مرتين `STOP_EARTH_UNDER_DECISION.bat` لإيقاف الخدمات مع الاحتفاظ بالبيانات.
- اضغط مرتين `VIEW_LOGS_EARTH_UNDER_DECISION.bat` لرؤية السجلات.
- لا تستخدم `docker compose down -v` إلا إذا كنت تريد حذف قاعدة البيانات وملفات المشروع المحفوظة في Docker volumes.

## ملف البيئة الوهمي

يوجد ملف `.env` في الحزمة بقيم `CHANGE_ME` الوهمية فقط. لا يحتوي كلمة مرور حقيقية ولا NASA token. للتجربة المحلية يمكن استخدام القيم الوهمية. قبل أي نشر عام يجب تعديل:

- `POSTGRES_PASSWORD`
- `ADMIN_API_TOKEN` (استخدم قيمة عشوائية من حروف وأرقام/Hex لتجنب محارف قد تربك ملف البيئة).

مع قيمة `CHANGE_ME` تظل عمليات الرفع والإدارة معطلة. لا تنسخ هذه القيم إلى الواجهة ولا تشاركها في المحادثة. ملف `.env` مستثنى من Git، و`.env.example` فقط هو الملف الآمن للرفع.

## الطريقة الثانية: نشر الموقع على الإنترنت من خلال لوحة رسومية

تم إعداد `render.yaml` لنشر Docker app واحد: FastAPI يقدم الموقع المبني من React من نفس النطاق، مع قاعدة PostgreSQL وقرص دائم للملفات. هذه تهيئة Blueprint؛ لم يتم إنشاء خدمة على حساب Render الخاص بك.

### المرحلة A — GitHub Desktop

1. ثبّت GitHub Desktop من `https://desktop.github.com/`.
2. سجّل الدخول.
3. فك الحزمة في مجلد دائم.
4. اختر `File → Add Local Repository`، ثم اختر مجلد المشروع.
5. إذا لم يكن مجلد Git جاهزًا، استخدم `create a repository` مع نفس المسار.
6. قبل أول Commit راجع الملفات: `.env` يجب ألا يظهر، بينما `.env.example` و`render.yaml` و`seed_data/` يجب أن تظهر.
7. أنشئ Commit ثم اضغط `Publish repository`. ابدأ بمستودع Private.

### المرحلة B — Render

1. افتح `https://dashboard.render.com/` وسجّل الدخول.
2. اختر `New → Blueprint` أو إنشاء Blueprint من Git repository.
3. اربط GitHub واختر مستودع `earth-under-decision`.
4. Render يقرأ `render.yaml`. راجع Web Service وPostgres وPersistent Disk والخطة/التكلفة المعروضة.
5. وافق على إنشاء الموارد وانتظر اكتمال Deployment.
6. افتح رابط `onrender.com` المعروض للخدمة.
7. اختبر `/health` ثم `/ready` ثم `/docs`، وبعدها صفحات الموقع.
8. تحقق من أن `ADMIN_API_TOKEN` تم توليده في Render Environment. لا ترسله لأحد ولا تضعه في frontend.

### تحديث الموقع بعد ذلك

من GitHub Desktop افتح المشروع، راجع Changes، أنشئ Commit ثم `Push origin`. Render يعيد النشر تلقائيًا عند وصول Commit جديد وفق إعداد Blueprint.

### الاحتفاظ بالبيانات

Render filesystem مؤقت بشكل افتراضي. تم ربط Persistent Disk على `/app/data`، ولذلك هذا المسار هو مكان التخزين المستمر لملفات Raw/Processed والملفات التي تُرفع لاحقًا. لا تغيّر مسار `LOCAL_STORAGE_ROOT` دون تعديل إعداد القرص. قاعدة البيانات منفصلة ومدارة بواسطة Render Postgres.

## التكلفة التقريبية عند استخدام Render

صفحة الأسعار الرسمية التي تمت مراجعتها في نوفمبر 2026 تعرض تقريبًا:

- Web Service `0.5c-512mb`: ‏7 USD شهريًا.
- Postgres `0.1c-256mb`: ‏6 USD شهريًا.
- Persistent Disk بحجم 1GB: ‏0.25 USD شهريًا.

التقدير الأساسي يقارب **13.25 USD شهريًا** قبل الضرائب أو الباندويث أو أي موارد إضافية. راجع السعر النهائي في لوحة Render قبل تأكيد الإنشاء، لأن الأسعار والخطط تتغير. لا تعتمد على Postgres المجاني لمخزن مستمر دون مراجعة قيود الانتهاء والاحتفاظ.

## حل المشاكل المعتادة

- إذا قال ملف START إن Docker غير مثبت: ثبّت Docker Desktop وافتحه.
- إذا قال إن Docker Engine غير شغال: افتح Docker Desktop وانتظر حتى يعمل Engine.
- إذا فشل بناء الصورة: راجع اتصال الإنترنت ثم اضغط START مرة أخرى.
- إذا لم يفتح الموقع: افتح Docker Desktop وتأكد أن `earth-under-decision-web` و`earth-under-decision-db` يعملان، ثم افتح ملف VIEW LOGS.
- إذا `/health` يعمل و`/ready` يفشل: راجع حالة Postgres/Migrations في السجلات.
- إذا ظهرت رسالة `processed_dataset_missing`: تأكد أن ملفات `seed_data/processed/` موجودة في النسخة التي رفعتها إلى GitHub وأن `LOCAL_STORAGE_ROOT=/app/data`.

## حدود النسخة الحالية

- الـFrontend وBackend متصلان من نفس الأصل في الـDocker deployment.
- بيانات GLDAS وGPM المتاحة من 2023 تظهر من API.
- NOAA يظهر كمرجع خارجي فقط وليس بيانات NASA.
- NDVI وLST ليس لهما ملفات فعلية في الدفعة المستلمة.
- الخريطة تعرض مراكز خلايا GPM ونقطة GLDAS ولا تخترع حدود محافظات.
- الصفحة الزمنية تصف موسمية 2023 فقط، ولا تحسب اتجاهًا مناخيًا طويل الأجل أو تنبؤًا.
- يلزم بعد أول تشغيل اختبار Docker فعلي على جهازك؛ بيئة البناء التي أنشأت الحزمة لم يتوفر بها Docker engine أو npm registry.
