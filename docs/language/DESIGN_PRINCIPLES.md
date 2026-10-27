# Nine Pillars of NolQu-L

## Pillar 1 — Kesederhanaan

NolQu-L harus memungkinkan programmer mengekspresikan program dengan cara yang sesederhana mungkin tanpa mengorbankan fungsi, kontrol, performa, maupun kejelasan. Bahasa tidak boleh memaksa programmer menulis sintaks, boilerplate, pola, atau aturan tambahan yang tidak memberikan manfaat nyata. Masalah yang sederhana harus dapat ditulis secara sederhana. Masalah yang memang kompleks boleh membutuhkan kode yang kompleks, tetapi NolQu-L tidak boleh menambahkan kompleksitas yang sebenarnya tidak diperlukan. Kesederhanaan bukan berarti kode harus menjadi sependek mungkin; tujuannya adalah menghilangkan kompleksitas yang tidak perlu sambil mempertahankan kompleksitas yang memang berasal dari masalah yang sedang diselesaikan.

## Pillar 2 — Keterbacaan

Kode NolQu-L harus mudah dibaca dan dipahami oleh manusia. Maksud, struktur, dan alur program harus sebisa mungkin terlihat jelas dari kode yang ditulis, sehingga pembaca tidak perlu menebak perilaku tersembunyi atau memahami aturan yang tidak intuitif hanya untuk mengetahui apa yang dilakukan program. NolQu-L tidak mengutamakan kode yang paling pendek apabila pemendekan tersebut membuat kode lebih sulit dipahami. Sintaks dan fitur bahasa harus mendorong kode yang jelas, konsisten, dan mudah diikuti, baik oleh penulisnya sendiri maupun oleh programmer lain pada masa mendatang.

## Pillar 3 — Dekat dengan Mesin

NolQu-L menargetkan kontrol setingkat assembly pada ISA yang didukung dan harus tetap transparan terhadap perilaku mesin di bawahnya. Hindari abstraksi yang menyembunyikan biaya sebenarnya — seperti alokasi memori, syscall, akses memori, dan operasi tingkat rendah lainnya.

Pengguna harus dapat memahami dan memperkirakan apa yang terjadi pada level mesin dari kode yang mereka tulis.

## Pillar 4 — Kompleks di Dalam, Mudah di Luar

Implementasi internal boleh rumit apabila memang diperlukan, tetapi antarmuka yang dilihat pengguna harus tetap sederhana, konsisten, dan intuitif.

Beban kompleksitas sebisa mungkin ditanggung oleh compiler dan runtime, bukan oleh pengguna.

## Pillar 5 — NolQu-L Safety

NolQu-L mengutamakan keamanan memori (memory safety) sebagai bagian dari desain bahasa melalui NolQu-L Safety — model keamanan yang dirancang untuk memberikan keamanan memori dan resource tanpa mengorbankan kesederhanaan, keterbacaan, performa, maupun kedekatan dengan mesin.

Seluruh desain NolQu-L Safety harus tetap mengikuti Nine Pillars of NolQu-L, terutama Pillar 1, Pillar 3, dan Pillar 4. NolQu-L Safety adalah identitas keamanan NolQu-L sendiri — terinspirasi oleh berbagai teknik yang telah terbukti di industri, tetapi diimplementasikan sesuai filosofi dan kebutuhan NolQu-L.

### Safe by Default

NolQu-L Safety dirancang dengan filosofi Safe by Default, di mana keamanan menjadi perilaku bawaan bahasa. Secara default NolQu-L menggunakan mode Balanced, yang mempertahankan jaminan keamanan inti sambil memberikan keseimbangan antara keamanan, fleksibilitas, dan performa.

Compiler melakukan sebanyak mungkin analisis saat kompilasi untuk mencegah berbagai kesalahan umum tanpa membebani programmer.

Analisis yang dilakukan compiler mencakup:

- Akses memori di luar batas (out-of-bounds).

- Penggunaan nilai yang belum diinisialisasi.

- Use-after-free dan double-free.

- Dangling pointer.

- Pemeriksaan nilai yang mungkin tidak ada secara eksplisit — nilai semacam ini harus direpresentasikan sebagai tipe dan tidak bisa diabaikan tanpa penanganan yang disengaja.

- Deteksi memory leak apabila memungkinkan.

- Pelepasan resource seperti memori, file, handle, dan resource lainnya secara otomatis ketika memungkinkan — deterministik, bukan bergantung pada garbage collector.

Resource dilepas di semua jalur, termasuk jalur error — tidak hanya di jalur sukses. Urutan pelepasan resource adalah kebalikan dari urutan alokasi — bisa diprediksi dan konsisten.

### Tiga Mode Keamanan

NolQu-L Safety menyediakan tiga mode keamanan yang bisa dipilih sesuai kebutuhan. Ketiga mode menggunakan fondasi NolQu-L Safety yang sama — perbedaannya terletak pada tingkat pemeriksaan, fleksibilitas, dan kontrol yang diberikan kepada programmer.

#### BALANCED (mode bawaan)

Mode default NolQu-L. Memberikan keseimbangan antara keamanan, fleksibilitas, dan performa, dengan tetap mempertahankan jaminan keamanan inti. Cocok untuk pengembangan aplikasi umum.

#### SAFE

Mengaktifkan analisis keamanan secara maksimal sesuai kemampuan compiler. Digunakan untuk kebutuhan yang mengutamakan keandalan dan keamanan di atas fleksibilitas.

#### UNSAFE

Memberikan kontrol tingkat rendah yang lebih besar dengan mengurangi jaminan keamanan. Cocok untuk pengembangan kernel, driver, interoperabilitas dengan bahasa lain, maupun optimasi khusus yang tidak bisa dicapai di mode lain. Mendekati kontrol C/C++, tetapi tetap eksplisit dan berada di bawah sistem NolQu-L Safety.

Penggunaan mode ini ditulis secara eksplisit di level file, modul, atau blok — bukan tersembunyi di konfigurasi build.

### Blok Unsafe

Untuk kebutuhan pemrograman tingkat rendah maupun optimasi tertentu, NolQu-L menyediakan blok unsafe yang memberikan kontrol lebih besar kepada programmer.

Aturan blok unsafe:

- Penggunaan blok unsafe secara eksplisit menandakan bahwa tanggung jawab terhadap keamanan berada pada programmer, bukan compiler.

- Compiler tetap melakukan analisis dan memberikan peringatan apabila memungkinkan, bahkan di dalam blok unsafe.

- Blok unsafe harus sekecil mungkin dan terisolasi — bukan jalan pintas untuk menghindari pemeriksaan keamanan.

- Setiap blok unsafe wajib disertai komentar yang menjelaskan mengapa kode tersebut tetap aman meski tidak bisa diverifikasi sepenuhnya oleh compiler (safety invariant):

```text
unsafe {
    -- safety: pointer valid karena dijamin oleh ...
    *ptr = 42
}
```

### Error yang Jelas

Setiap pelanggaran NolQu-L Safety harus menghasilkan pesan error yang menyebutkan:

- Kode error NolQu-L Safety (NS-xxx) untuk referensi dokumentasi.

- Lokasi kejadian (file, baris, kolom).

- Apa yang dilanggar dan mengapa itu masalah.

- Apa yang bisa dilakukan untuk memperbaikinya.

Pelanggaran NolQu-L Safety yang dapat dibuktikan tidak boleh lolos tanpa diagnostic yang sesuai. Perilaku yang berada di luar safety guarantees harus dinyatakan secara eksplisit dan tetap dapat dilacak.

### Keamanan dan Performa Bukan Pertentangan

Pemeriksaan NolQu-L Safety dilakukan sedini mungkin, terutama saat kompilasi. Pemeriksaan runtime digunakan hanya ketika properti tersebut tidak dapat dibuktikan secara statis dan pemeriksaan runtime memang diperlukan. Biaya performa keamanan di NolQu-L harus terukur, transparan, dan dapat diprediksi — sesuai Pillar 3.

### Urutan Implementasi di Compiler

NolQu-L Safety diimplementasikan bertahap, dimulai dari yang paling fundamental:

1. Pelepasan resource otomatis dan deteksi use-after-free.

2. Pemeriksaan nilai tidak terinisialisasi dan out-of-bounds.

3. Model kepemilikan (ownership) dan move semantics.

4. Pemeriksaan peminjaman (borrow checking).

5. Verifikasi lifetime dan dangling pointer.

6. Tiga mode keamanan (Balanced, Safe, Unsafe).

Setiap tahap harus stabil sebelum tahap berikutnya dimulai.

## Pillar 6 — Penanganan Error yang Jelas

Setiap error harus memberikan:

- Lokasi terjadinya error (file, baris, kolom).

- Penyebab error.

- Dan jika memungkinkan, saran konkret untuk memperbaikinya.

Tidak boleh ada kegagalan diam-diam maupun crash tanpa konteks yang jelas. Error merupakan bagian dari antarmuka bahasa, bukan sekadar fitur tambahan.

Ini berlaku untuk semua lapisan: lexer, parser, NolQu-L Safety, linker, dan runtime. Tidak ada lapisan yang boleh menghasilkan pesan yang tidak bisa dipahami pengguna.

## Pillar 7 — Test Sebelum Merge

Tidak ada perubahan yang boleh masuk tanpa test yang membuktikan bahwa perubahan tersebut bekerja dengan benar dan tidak menyebabkan regresi yang tidak disengaja pada bagian lain.

Setiap perubahan harus memiliki pengujian yang sesuai dengan dampaknya, termasuk apabila perubahan tersebut secara sengaja mengubah perilaku lama.

Jika regresi yang tidak disengaja ditemukan saat implementasi, hentikan — perbaiki regresi tersebut sebelum melanjutkan.

Breaking change yang telah direncanakan dan disetujui berdasarkan Pillar 8 tidak dianggap sebagai regresi, tetapi tetap wajib memiliki test yang membuktikan bahwa:

- Perilaku baru bekerja sesuai desain.

- Bagian lain tidak rusak secara tidak disengaja.

- Perubahan memberikan manfaat yang menjadi alasan breaking change.

- Jalur migrasi bekerja apabila jalur tersebut disediakan.

Test bukan hanya alat untuk mempertahankan perilaku lama. Test juga menjadi bukti bahwa evolusi bahasa dilakukan secara terkendali.

## Pillar 8 — Stabilitas Tanpa Menghambat Evolusi

Perubahan harus sebisa mungkin menjaga kompatibilitas dan tidak merusak kode yang sudah bekerja. Namun, backward compatibility bukan tujuan absolut.

Stabilitas adalah default — bukan batas yang mencegah bahasa berkembang.

Perubahan yang mematahkan kompatibilitas diperbolehkan apabila memberikan peningkatan yang berarti terhadap:

- Keamanan.

- Kesederhanaan.

- Keterbacaan.

- Performa.

- Konsistensi bahasa.

- Kemampuan compiler melakukan analisis.

- Maintainability.

- Kualitas arsitektur jangka panjang.

NolQu-L tidak boleh mempertahankan keputusan desain yang buruk hanya demi kompatibilitas.

### Breaking Change Harus Memiliki Alasan

Breaking change tidak boleh dilakukan hanya karena desain baru terlihat lebih menarik atau lebih modern.

Setiap breaking change harus memiliki alasan teknis yang jelas dan manfaat yang cukup besar untuk membenarkan biaya migrasinya.

Sebelum breaking change diterima, setidaknya harus diketahui:

- Masalah pada desain atau perilaku lama.

- Alasan mengapa masalah tersebut perlu diperbaiki.

- Manfaat dari desain baru.

- Bagian bahasa atau ekosistem yang terdampak.

- Risiko yang ditimbulkan.

- Alternatif yang telah dipertimbangkan.

Semakin luas dampak perubahan, semakin kuat alasan yang diperlukan.

### Kompatibilitas Memiliki Beberapa Bentuk

Kompatibilitas bukan hanya tentang apakah source code lama masih dapat dikompilasi. Perubahan dapat memengaruhi:

- Source compatibility.

- Behavior compatibility.

- Binary atau ABI compatibility.

- Library compatibility.

- Tooling compatibility.

- Interoperability dengan sistem lain.

Dampak terhadap masing-masing bagian harus dipertimbangkan sesuai konteks perubahan. NolQu-L tidak menjanjikan bahwa seluruh bentuk kompatibilitas harus selalu dipertahankan, tetapi compiler dan ekosistem tidak boleh mematahkannya tanpa alasan yang diketahui.

### Migration Path

Jika memungkinkan, breaking change harus menyediakan jalur migrasi yang masuk akal.

Jalur migrasi dapat berupa:

- Diagnostic compiler yang menjelaskan perubahan.

- Saran pengganti untuk sintaks atau API lama.

- Automatic fix atau migration tooling.

- Compatibility layer sementara.

- Dokumentasi migrasi.

- Periode deprecation sebelum fitur dihapus.

Namun, migration path bukan kewajiban absolut apabila mempertahankan mekanisme lama justru:

- Menciptakan risiko keamanan.

- Membuat implementasi jauh lebih kompleks.

- Menyebabkan perilaku ambigu.

- Menghambat arsitektur baru.

- Bertentangan dengan Nine Pillars of NolQu-L.

Dalam kondisi tersebut, perubahan langsung tetap diperbolehkan selama alasannya terdokumentasi dengan jelas.

### Deprecation Sebelum Removal

Fitur yang masih aman dan masih dapat dipertahankan dengan biaya yang wajar sebaiknya melalui proses deprecation sebelum dihapus.

Compiler dapat memberikan warning yang menjelaskan:

- Bahwa fitur tersebut deprecated.

- Alasan deprecation.

- Alternatif yang direkomendasikan.

- Versi ketika fitur tersebut direncanakan untuk dihapus, apabila sudah diketahui.

Deprecation tidak boleh menjadi tempat permanen bagi desain lama. Jika suatu fitur telah memiliki pengganti yang lebih baik dan alasan keberadaannya tidak lagi cukup kuat, fitur tersebut pada akhirnya dapat dihapus.

### Hindari Compatibility Debt

Kompatibilitas memiliki biaya. Compatibility shim, legacy behavior, parser khusus untuk sintaks lama, maupun jalur compiler tambahan dapat meningkatkan kompleksitas implementasi dan maintenance.

NolQu-L tidak boleh terus menambahkan lapisan kompatibilitas sampai compiler menjadi lebih sulit dipahami, diuji, dioptimalkan, atau dikembangkan.

Jika biaya mempertahankan kompatibilitas mulai lebih besar daripada manfaatnya, desain tersebut harus dievaluasi kembali. Menghapus compatibility debt diperbolehkan apabila memberikan perbaikan arsitektur yang nyata dan mengikuti aturan breaking change pada pillar ini.

### Breaking Change Harus Terkendali

Breaking change harus dilakukan secara eksplisit dan terencana. Perubahan besar sebisa mungkin dikumpulkan pada batas versi yang jelas daripada muncul secara acak di banyak update kecil.

Pengguna harus dapat mengetahui bahwa suatu versi membawa perubahan yang membutuhkan migrasi.

Compiler tidak boleh diam-diam mengubah arti kode lama apabila perubahan tersebut dapat menghasilkan perilaku yang berbeda tanpa diagnostic yang memadai.

### Evolusi Tanpa Rewrite Tanpa Alasan

Kebebasan melakukan breaking change bukan izin untuk terus mendesain ulang bahasa. Bagian yang sudah bekerja dengan baik tidak perlu diubah hanya demi konsistensi kosmetik, preferensi pribadi, atau tren bahasa pemrograman lain.

Perubahan harus menyelesaikan masalah nyata atau memberikan peningkatan yang cukup berarti.

> Pertahankan yang baik.\
> Perbaiki yang buruk.\
> Ganti yang menghambat masa depan.

Stabilitas harus melindungi pengguna dari perubahan yang tidak perlu. Evolusi harus melindungi bahasa dari keputusan lama yang tidak lagi layak dipertahankan.

## Pillar 9 — Optimasi Berdasarkan Dampak

Optimasi struktural dianjurkan apabila terdapat peluang nyata untuk memberikan dampak yang signifikan terhadap performa, penggunaan memori, ukuran binary, waktu kompilasi, atau kualitas arsitektur.

Optimasi mikro yang dampaknya belum diukur atau tidak terbukti tidak perlu dipaksakan.

Optimasi yang meningkatkan kompleksitas implementasi harus memiliki manfaat yang sebanding dengan biaya maintenance yang ditimbulkannya.

Jika sebuah optimasi membutuhkan breaking change, perubahan tersebut juga harus memenuhi Pillar 8. Dengan demikian, "lebih cepat" saja tidak otomatis menjadi alasan untuk mematahkan kompatibilitas.

Semakin besar biaya perubahan bagi pengguna, semakin besar pula peningkatan yang harus dapat dibuktikan. Optimasi harus berdasarkan dampak nyata — bukan sekadar kemungkinan teoritis.
