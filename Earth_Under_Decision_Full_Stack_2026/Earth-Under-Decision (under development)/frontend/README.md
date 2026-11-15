# Earth Under Decision — الواجهة الأمامية

نسخة Frontend مستقلة لمشروع **Earth Under Decision** — فريق NON-HUMAN، مبنية حسب ملف الـFrontend Master Prompt.

## الصفحات الموجودة

- الصفحة الرئيسية Landing Page.
- لوحة المعلومات Dashboard.
- الخريطة التفاعلية Explore Map.
- تحليل الاتجاهات Trend Analysis.
- التحليل الافتراضي What-If Analysis.
- المنهجية ومصادر البيانات Methodology & Data Sources.

## التقنيات

- React 18 + TypeScript.
- Vite.
- React Router.
- MapLibre GL.
- Lucide Icons.
- CSS design system مخصص.

## التشغيل على جهازك

المتطلبات: Node.js 20 أو أحدث، وnpm.

```bash
npm install
npm run dev
```

بعدها افتح العنوان الذي يظهر في Terminal (غالبًا `http://localhost:5173`).

لإنشاء نسخة Production:

```bash
npm run build
npm run preview
```

## حالة النسخة الحالية — مهم

هذه **واجهة Frontend فقط**. لا يوجد Backend أو Database أو تسجيل دخول أو NASA data ingestion أو Raster processing أو حسابات علمية متصلة.

- مؤشرات Dashboard تعرض حالة عدم توافر بيانات موثقة بدل اختراع قياسات.
- الخريطة تستخدم CARTO dark basemap كمرجع جغرافي فقط، وليست طبقة رصد بيئي أو قياسات NASA.
- نقاط مناطق الدراسة تقريبية ومرشحة، وليست حدودًا إدارية تم التحقق منها.
- اختيار NDVI / LST / GPM يغيّر اختيار الواجهة فقط إلى أن تتصل طبقات البيانات الحقيقية.
- اختيار LST Daytime / Nighttime موجود، لكنه لا يعرض Raster حقيقيًا بعد.
- Trend Analysis لا يخترع سلسلة زمنية أو معدل تغير أو دلالة إحصائية.
- What-If مجرد إعداد افتراضي توضيحي، وليس نموذج تنبؤ.
- مجموعات بيانات MODIS وGPM معروضة كمصادر مرشحة؛ الواجهة لا تدعي أنها حُمّلت أو فُحصت.

قبل تقديم المنصة كحل علمي في المسابقة، يجب ربط البيانات الفعلية والتحقق منها، ثم استبدال حالات عدم التوافر بنتائج موثقة ومخرجات تحليل حقيقية.

## ملاحظات

الخرائط والصور والخطوط تُحمّل من خدمات خارجية، ولذلك تحتاج إلى اتصال بالإنترنت. لا تحتاج الخريطة إلى مفتاح API مدفوع. يجب التأكد من إسناد الصور إلى مصدرها الصحيح قبل النشر النهائي.


## الاتصال بالـBackend

بعد تشغيل الـBackend على `http://localhost:8000`، انسخ `frontend/.env.example` إلى `frontend/.env` عند الحاجة، واضبط `VITE_API_BASE_URL`. لا تضع أي API token أو NASA credentials في متغيرات `VITE_`؛ هذه القيم تُرسل إلى كود المتصفح.

تقرأ الواجهة حالة الخادم وملخص الـDashboard وكتالوج الـDatasets وطبقات الخريطة ونتائج Trend Analysis من الـAPI. تحفظ What-If assumptions في الـBackend بوصفها `illustrative_only` دون حساب أو توقع بيئي.
