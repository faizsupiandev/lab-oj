#!/usr/bin/env python3
"""Seed more questions into question_bank. Run with: python3 /tmp/seed_more.py"""
import sqlite3, json, os

DB_PATH = os.getenv("DB_PATH", "/data/lab.db")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys=ON")

def q(title, desc, course, chapter, diff, tmpl, inp_fmt, out_fmt, sample_in, sample_out, tests):
    try:
        conn.execute("""INSERT INTO question_bank
            (title, description, course_code, chapter, difficulty, default_template,
             input_format, output_format, sample_input, sample_output, hidden_tests, time_limit_sec)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (title, desc, course, chapter, diff, tmpl, inp_fmt, out_fmt, sample_in, sample_out,
             json.dumps(tests), 5.0))
        print(f"  OK: [{course} Ch{chapter}] {title}")
    except Exception as e:
        print(f"  ERR: {title} => {e}")

CPP = "#include <iostream>\nusing namespace std;\nint main() {\n    // tulis kod anda di sini\n    return 0;\n}"
CPP_STR = "#include <iostream>\n#include <string>\nusing namespace std;\nint main() {\n    string s;\n    cin >> s;\n    // tulis kod anda di sini\n    return 0;\n}"
CPP_IOMANIP = "#include <iostream>\n#include <iomanip>\nusing namespace std;\nint main() {\n    // tulis kod anda di sini\n    return 0;\n}"
CPP_FN = "#include <iostream>\nusing namespace std;\n\n// define function here\n\nint main() {\n    // tulis kod anda di sini\n    return 0;\n}"
CPP_FN_STR = "#include <iostream>\n#include <string>\nusing namespace std;\n\n// define function here\n\nint main() {\n    // tulis kod anda di sini\n    return 0;\n}"

print("=== BITP1113 Ch1 (add 4) ===")
q("Print 10 Asterisks",
  "Tulis program C++ yang mencetak satu baris mengandungi 10 asterisk (*) tanpa sebarang input.",
  "BITP1113", 1, "Mudah", CPP,
  "Tiada input.", "Cetak satu baris: **********",
  "", "**********",
  [{"input": "", "expected_output": "**********"},
   {"input": "", "expected_output": "**********"},
   {"input": "", "expected_output": "**********"}])

q("Hello Name",
  "Baca nama pengguna dari input dan cetak mesej 'Hello, [nama]!' ke output standard.",
  "BITP1113", 1, "Mudah", CPP_STR,
  "Satu perkataan: nama pengguna.", "Cetak satu baris: Hello, [nama]!",
  "Ahmad", "Hello, Ahmad!",
  [{"input": "Ahmad", "expected_output": "Hello, Ahmad!"},
   {"input": "Siti", "expected_output": "Hello, Siti!"},
   {"input": "John", "expected_output": "Hello, John!"},
   {"input": "Ali", "expected_output": "Hello, Ali!"}])

q("Print University Info",
  "Cetak 3 baris yang mengandungi nama universiti, fakulti, dan program anda (nilai tetap: UTEM, FTMK, BITP).",
  "BITP1113", 1, "Mudah", CPP,
  "Tiada input.", "Cetak 3 baris: UTEM, FTMK, BITP",
  "", "UTEM\nFTMK\nBITP",
  [{"input": "", "expected_output": "UTEM\nFTMK\nBITP"},
   {"input": "", "expected_output": "UTEM\nFTMK\nBITP"},
   {"input": "", "expected_output": "UTEM\nFTMK\nBITP"}])

q("Reverse Two Integers",
  "Baca dua integer a dan b dari input, kemudian cetak mereka dalam susunan terbalik (b dahulu, kemudian a).",
  "BITP1113", 1, "Mudah", CPP,
  "Satu baris: dua integer a dan b dipisah ruang.", "Cetak dua integer: b kemudian a, dipisah ruang.",
  "3 7", "7 3",
  [{"input": "3 7", "expected_output": "7 3"},
   {"input": "10 20", "expected_output": "20 10"},
   {"input": "0 5", "expected_output": "5 0"},
   {"input": "100 1", "expected_output": "1 100"}])

print("=== BITP1113 Ch2 (add 4) ===")
q("Smallest of Three Numbers",
  "Baca tiga nombor integer dan cetak yang paling kecil di antara ketiganya.",
  "BITP1113", 2, "Mudah", CPP,
  "Satu baris: tiga integer dipisah ruang.", "Cetak satu integer: nilai paling kecil.",
  "5 3 8", "3",
  [{"input": "5 3 8", "expected_output": "3"},
   {"input": "1 2 3", "expected_output": "1"},
   {"input": "7 7 7", "expected_output": "7"},
   {"input": "0 -1 3", "expected_output": "-1"},
   {"input": "10 5 8", "expected_output": "5"}])

q("Circle Area",
  "Baca jejari bulatan dan cetak luas bulatan. Gunakan pi = 3.14159 dan formula: luas = pi * r * r. Cetak dengan 2 tempat perpuluhan.",
  "BITP1113", 2, "Sederhana", CPP_IOMANIP,
  "Satu baris: satu integer r (jejari).", "Cetak satu nombor perpuluhan: luas bulatan (2 d.p.).",
  "7", "153.94",
  [{"input": "7", "expected_output": "153.94"},
   {"input": "1", "expected_output": "3.14"},
   {"input": "5", "expected_output": "78.54"},
   {"input": "10", "expected_output": "314.16"}])

q("Speed Calculator",
  "Baca jarak (km) dan masa (jam), kemudian kira dan cetak halaju dalam km/j. Cetak dengan 2 tempat perpuluhan.",
  "BITP1113", 2, "Mudah", CPP_IOMANIP,
  "Satu baris: dua integer - jarak (km) dan masa (jam).", "Cetak satu nombor perpuluhan: halaju (km/j) dengan 2 d.p.",
  "100 2", "50.00",
  [{"input": "100 2", "expected_output": "50.00"},
   {"input": "150 3", "expected_output": "50.00"},
   {"input": "200 4", "expected_output": "50.00"},
   {"input": "300 2", "expected_output": "150.00"},
   {"input": "60 1", "expected_output": "60.00"}])

q("Total Cost",
  "Baca harga (integer) dan kuantiti (integer), kemudian cetak jumlah kos (harga * kuantiti).",
  "BITP1113", 2, "Mudah", CPP,
  "Satu baris: dua integer - harga dan kuantiti.", "Cetak satu integer: jumlah kos.",
  "25 4", "100",
  [{"input": "25 4", "expected_output": "100"},
   {"input": "10 5", "expected_output": "50"},
   {"input": "100 1", "expected_output": "100"},
   {"input": "7 7", "expected_output": "49"},
   {"input": "0 10", "expected_output": "0"}])

print("=== BITP1113 Ch3 (add 4) ===")
q("Square and Cube",
  "Baca satu integer n, kemudian cetak kuasadua (n*n) dan kuasatiga (n*n*n) masing-masing pada baris berasingan.",
  "BITP1113", 3, "Mudah", CPP,
  "Satu baris: satu integer n.", "Cetak dua baris: kuasadua n pada baris pertama, kuasatiga n pada baris kedua.",
  "4", "16\n64",
  [{"input": "4", "expected_output": "16\n64"},
   {"input": "3", "expected_output": "9\n27"},
   {"input": "1", "expected_output": "1\n1"},
   {"input": "5", "expected_output": "25\n125"},
   {"input": "2", "expected_output": "4\n8"}])

q("Average of Three Floats",
  "Baca tiga nombor perpuluhan (float), kira purata mereka dan cetak dengan 2 tempat perpuluhan menggunakan setprecision.",
  "BITP1113", 3, "Mudah", CPP_IOMANIP,
  "Satu baris: tiga nombor perpuluhan dipisah ruang.", "Cetak satu nombor perpuluhan: purata dengan 2 d.p.",
  "3.0 5.0 7.0", "5.00",
  [{"input": "3.0 5.0 7.0", "expected_output": "5.00"},
   {"input": "1.0 2.0 3.0", "expected_output": "2.00"},
   {"input": "1.5 2.5 3.0", "expected_output": "2.33"},
   {"input": "10.0 20.0 30.0", "expected_output": "20.00"},
   {"input": "0.0 0.0 0.0", "expected_output": "0.00"}])

q("Integer Division and Modulo",
  "Baca dua integer a dan b, kemudian cetak hasil bahagi bulat (a / b) pada baris pertama dan baki (a % b) pada baris kedua.",
  "BITP1113", 3, "Mudah", CPP,
  "Satu baris: dua integer a dan b dipisah ruang (b != 0).", "Cetak dua baris: a/b pada baris pertama, a%b pada baris kedua.",
  "10 3", "3\n1",
  [{"input": "10 3", "expected_output": "3\n1"},
   {"input": "20 4", "expected_output": "5\n0"},
   {"input": "7 2", "expected_output": "3\n1"},
   {"input": "100 7", "expected_output": "14\n2"},
   {"input": "15 5", "expected_output": "3\n0"}])

q("Triangle Area",
  "Baca tapak dan tinggi segitiga, kemudian kira dan cetak luasnya. Formula: luas = 0.5 * tapak * tinggi. Cetak dengan 2 tempat perpuluhan.",
  "BITP1113", 3, "Mudah", CPP_IOMANIP,
  "Satu baris: dua nombor - tapak dan tinggi segitiga.", "Cetak satu nombor perpuluhan: luas segitiga dengan 2 d.p.",
  "6 4", "12.00",
  [{"input": "6 4", "expected_output": "12.00"},
   {"input": "5 8", "expected_output": "20.00"},
   {"input": "3 3", "expected_output": "4.50"},
   {"input": "10 5", "expected_output": "25.00"},
   {"input": "1 1", "expected_output": "0.50"}])

print("=== BITP1113 Ch4 (add 2) ===")
q("Largest of Three Numbers",
  "Baca tiga integer dan cetak yang paling besar menggunakan if-else.",
  "BITP1113", 4, "Mudah", CPP,
  "Satu baris: tiga integer dipisah ruang.", "Cetak satu integer: nilai paling besar.",
  "5 12 8", "12",
  [{"input": "5 12 8", "expected_output": "12"},
   {"input": "1 2 3", "expected_output": "3"},
   {"input": "9 9 9", "expected_output": "9"},
   {"input": "-1 -5 -2", "expected_output": "-1"},
   {"input": "100 50 75", "expected_output": "100"}])

q("Leap Year Check",
  "Baca satu integer (tahun) dan tentukan sama ada ia tahun lompat atau bukan. Tahun lompat: boleh dibahagi dengan 4 DAN (tidak boleh dibahagi 100 ATAU boleh dibahagi 400). Cetak 'Leap Year' atau 'Not a Leap Year'.",
  "BITP1113", 4, "Sederhana", CPP,
  "Satu baris: satu integer - tahun.", "Cetak satu baris: 'Leap Year' atau 'Not a Leap Year'.",
  "2024", "Leap Year",
  [{"input": "2024", "expected_output": "Leap Year"},
   {"input": "2023", "expected_output": "Not a Leap Year"},
   {"input": "2000", "expected_output": "Leap Year"},
   {"input": "1900", "expected_output": "Not a Leap Year"},
   {"input": "2100", "expected_output": "Not a Leap Year"}])

print("=== BITP1113 Ch5 (add 2) ===")
q("Even Numbers from 2 to N",
  "Baca integer N dan cetak semua nombor genap dari 2 hingga N (setiap nombor pada baris berasingan). Jika N < 2, tiada output.",
  "BITP1113", 5, "Mudah", CPP,
  "Satu baris: satu integer N.", "Cetak nombor genap dari 2 hingga N, setiap satu pada baris berasingan.",
  "10", "2\n4\n6\n8\n10",
  [{"input": "10", "expected_output": "2\n4\n6\n8\n10"},
   {"input": "6", "expected_output": "2\n4\n6"},
   {"input": "2", "expected_output": "2"},
   {"input": "1", "expected_output": ""},
   {"input": "8", "expected_output": "2\n4\n6\n8"}])

q("Sum and Average of N Integers",
  "Baca integer N, kemudian baca N integer. Cetak jumlah (sum) pada baris pertama dan purata (average) dengan 2 tempat perpuluhan pada baris kedua.",
  "BITP1113", 5, "Sederhana", CPP_IOMANIP,
  "Baris pertama: N. Baris kedua: N integer dipisah ruang.", "Cetak dua baris: jumlah pada baris pertama, purata (2 d.p.) pada baris kedua.",
  "3\n1 2 3", "6\n2.00",
  [{"input": "3\n1 2 3", "expected_output": "6\n2.00"},
   {"input": "4\n10 20 30 40", "expected_output": "100\n25.00"},
   {"input": "5\n1 1 1 1 1", "expected_output": "5\n1.00"},
   {"input": "1\n7", "expected_output": "7\n7.00"},
   {"input": "2\n3 7", "expected_output": "10\n5.00"}])

print("=== BITP1113 Ch6 (add 3) ===")
q("isPrime Function",
  "Tulis fungsi isPrime(int n) yang mengembalikan true jika n adalah nombor perdana dan false jika sebaliknya. Baca n dan cetak 'Prime' atau 'Not Prime'.",
  "BITP1113", 6, "Sederhana",
  "#include <iostream>\nusing namespace std;\n\nbool isPrime(int n) {\n    // tulis kod fungsi di sini\n}\n\nint main() {\n    int n;\n    cin >> n;\n    // panggil fungsi dan cetak keputusan\n    return 0;\n}",
  "Satu baris: satu integer n.", "Cetak satu baris: 'Prime' atau 'Not Prime'.",
  "7", "Prime",
  [{"input": "7", "expected_output": "Prime"},
   {"input": "4", "expected_output": "Not Prime"},
   {"input": "2", "expected_output": "Prime"},
   {"input": "1", "expected_output": "Not Prime"},
   {"input": "13", "expected_output": "Prime"},
   {"input": "9", "expected_output": "Not Prime"}])

q("Power Function (Loop)",
  "Tulis fungsi power(int base, int exp) yang mengira dan mengembalikan base dipangkatkan exp menggunakan gelung (bukan rekursion). Baca base dan exp, kemudian cetak hasilnya.",
  "BITP1113", 6, "Sederhana",
  "#include <iostream>\nusing namespace std;\n\nint power(int base, int exp) {\n    // tulis kod fungsi di sini (gunakan gelung, bukan rekursion)\n}\n\nint main() {\n    int base, exp;\n    cin >> base >> exp;\n    cout << power(base, exp) << endl;\n    return 0;\n}",
  "Satu baris: dua integer - base dan exp.", "Cetak satu integer: base dipangkatkan exp.",
  "2 10", "1024",
  [{"input": "2 10", "expected_output": "1024"},
   {"input": "3 4", "expected_output": "81"},
   {"input": "5 3", "expected_output": "125"},
   {"input": "1 100", "expected_output": "1"},
   {"input": "2 0", "expected_output": "1"}])

q("Absolute Value Function",
  "Tulis fungsi absolute(int x) yang mengembalikan nilai mutlak (absolute value) bagi x. Baca satu integer dan cetak nilai mutlaknya.",
  "BITP1113", 6, "Mudah",
  "#include <iostream>\nusing namespace std;\n\nint absolute(int x) {\n    // tulis kod fungsi di sini\n}\n\nint main() {\n    int x;\n    cin >> x;\n    cout << absolute(x) << endl;\n    return 0;\n}",
  "Satu baris: satu integer.", "Cetak satu integer: nilai mutlak.",
  "-5", "5",
  [{"input": "-5", "expected_output": "5"},
   {"input": "3", "expected_output": "3"},
   {"input": "0", "expected_output": "0"},
   {"input": "-100", "expected_output": "100"},
   {"input": "7", "expected_output": "7"}])

print("=== DFDS1513 Ch1 (add 3) ===")
q("Print Personal Info",
  "Cetak 5 baris maklumat berikut (nilai tetap): Name: Ahmad bin Ali, Matric: B00CS0001, Course: DFDS1513, Faculty: FTMK, University: UTeM",
  "DFDS1513", 1, "Mudah", CPP,
  "Tiada input.", "Cetak 5 baris maklumat peribadi.",
  "", "Name: Ahmad bin Ali\nMatric: B00CS0001\nCourse: DFDS1513\nFaculty: FTMK\nUniversity: UTeM",
  [{"input": "", "expected_output": "Name: Ahmad bin Ali\nMatric: B00CS0001\nCourse: DFDS1513\nFaculty: FTMK\nUniversity: UTeM"},
   {"input": "", "expected_output": "Name: Ahmad bin Ali\nMatric: B00CS0001\nCourse: DFDS1513\nFaculty: FTMK\nUniversity: UTeM"},
   {"input": "", "expected_output": "Name: Ahmad bin Ali\nMatric: B00CS0001\nCourse: DFDS1513\nFaculty: FTMK\nUniversity: UTeM"}])

q("Sum with Label",
  "Baca dua integer, kira jumlah mereka dan cetak hasilnya dalam format: 'Sum = X' di mana X ialah jumlah.",
  "DFDS1513", 1, "Mudah", CPP,
  "Satu baris: dua integer dipisah ruang.", "Cetak satu baris: Sum = X",
  "5 3", "Sum = 8",
  [{"input": "5 3", "expected_output": "Sum = 8"},
   {"input": "10 20", "expected_output": "Sum = 30"},
   {"input": "0 0", "expected_output": "Sum = 0"},
   {"input": "100 -50", "expected_output": "Sum = 50"},
   {"input": "7 3", "expected_output": "Sum = 10"}])

q("Good Morning Greeting",
  "Baca nama pengguna dan cetak mesej sapaan pagi: 'Good morning, [nama]!'",
  "DFDS1513", 1, "Mudah", CPP_STR,
  "Satu perkataan: nama pengguna.", "Cetak satu baris: Good morning, [nama]!",
  "Ahmad", "Good morning, Ahmad!",
  [{"input": "Ahmad", "expected_output": "Good morning, Ahmad!"},
   {"input": "Siti", "expected_output": "Good morning, Siti!"},
   {"input": "John", "expected_output": "Good morning, John!"},
   {"input": "Ali", "expected_output": "Good morning, Ali!"}])

print("=== DFDS1513 Ch2 (add 4) ===")
q("Exam Pass or Fail",
  "Baca 3 markah peperiksaan (integer). Untuk setiap markah, cetak 'Pass' jika markah >= 50 dan 'Fail' jika sebaliknya. Setiap keputusan pada baris berasingan.",
  "DFDS1513", 2, "Mudah", CPP,
  "Satu baris: tiga integer - markah1, markah2, markah3.", "Cetak tiga baris: 'Pass' atau 'Fail' untuk setiap markah.",
  "75 40 55", "Pass\nFail\nPass",
  [{"input": "75 40 55", "expected_output": "Pass\nFail\nPass"},
   {"input": "50 49 100", "expected_output": "Pass\nFail\nPass"},
   {"input": "0 0 0", "expected_output": "Fail\nFail\nFail"},
   {"input": "80 90 70", "expected_output": "Pass\nPass\nPass"},
   {"input": "50 50 50", "expected_output": "Pass\nPass\nPass"}])

q("Price with Tax",
  "Baca harga asal (integer) dan kadar cukai dalam peratus (integer). Kira harga akhir selepas cukai dan cetak dengan 2 tempat perpuluhan.",
  "DFDS1513", 2, "Mudah", CPP_IOMANIP,
  "Satu baris: dua integer - harga dan kadar cukai (%).", "Cetak satu nombor perpuluhan: harga akhir dengan 2 d.p.",
  "100 10", "110.00",
  [{"input": "100 10", "expected_output": "110.00"},
   {"input": "200 5", "expected_output": "210.00"},
   {"input": "50 0", "expected_output": "50.00"},
   {"input": "80 25", "expected_output": "100.00"},
   {"input": "1000 6", "expected_output": "1060.00"}])

q("Sum of Odd Numbers 1 to N",
  "Baca integer N dan cetak jumlah semua nombor ganjil dari 1 hingga N.",
  "DFDS1513", 2, "Mudah", CPP,
  "Satu baris: satu integer N.", "Cetak satu integer: jumlah nombor ganjil dari 1 hingga N.",
  "5", "9",
  [{"input": "5", "expected_output": "9"},
   {"input": "10", "expected_output": "25"},
   {"input": "1", "expected_output": "1"},
   {"input": "2", "expected_output": "1"},
   {"input": "7", "expected_output": "16"}])

q("Compare Two Numbers",
  "Baca dua integer a dan b. Cetak nombor yang lebih besar. Jika sama, cetak 'Equal'.",
  "DFDS1513", 2, "Mudah", CPP,
  "Satu baris: dua integer a dan b.", "Cetak nombor lebih besar atau 'Equal'.",
  "5 3", "5",
  [{"input": "5 3", "expected_output": "5"},
   {"input": "2 7", "expected_output": "7"},
   {"input": "4 4", "expected_output": "Equal"},
   {"input": "-1 -5", "expected_output": "-1"},
   {"input": "0 0", "expected_output": "Equal"}])

print("=== DFDS1513 Ch3 (add 3) ===")
q("Time Conversion (HH:MM:SS)",
  "Baca jumlah saat (integer) dan tukar ke format jam:minit:saat (HH:MM:SS). Cetak dalam format dua digit (gunakan leading zero jika perlu).",
  "DFDS1513", 3, "Sederhana", CPP_IOMANIP,
  "Satu baris: satu integer - jumlah saat.", "Cetak satu baris dalam format HH:MM:SS.",
  "3661", "01:01:01",
  [{"input": "3661", "expected_output": "01:01:01"},
   {"input": "3600", "expected_output": "01:00:00"},
   {"input": "7322", "expected_output": "02:02:02"},
   {"input": "59", "expected_output": "00:00:59"},
   {"input": "0", "expected_output": "00:00:00"}])

q("Circle Circumference",
  "Baca jejari bulatan dan cetak kelilingnya. Formula: keliling = 2 * pi * r, dengan pi = 3.14159. Cetak dengan 2 tempat perpuluhan.",
  "DFDS1513", 3, "Mudah", CPP_IOMANIP,
  "Satu baris: satu integer - jejari.", "Cetak satu nombor perpuluhan: keliling dengan 2 d.p.",
  "7", "43.98",
  [{"input": "7", "expected_output": "43.98"},
   {"input": "1", "expected_output": "6.28"},
   {"input": "5", "expected_output": "31.42"},
   {"input": "10", "expected_output": "62.83"}])

q("Absolute Value using Conditional Operator",
  "Baca satu integer dan cetak nilai mutlaknya menggunakan operator kondisional (?:) dalam C++.",
  "DFDS1513", 3, "Mudah", CPP,
  "Satu baris: satu integer.", "Cetak satu integer: nilai mutlak.",
  "-8", "8",
  [{"input": "-8", "expected_output": "8"},
   {"input": "5", "expected_output": "5"},
   {"input": "0", "expected_output": "0"},
   {"input": "-100", "expected_output": "100"},
   {"input": "42", "expected_output": "42"}])

print("=== DFDS1513 Ch4 (add 4 - void functions) ===")
q("printStars Function",
  "Tulis fungsi void printStars(int n) yang mencetak n asterisk (*) pada satu baris. Baca n dari input dan panggil fungsi tersebut.",
  "DFDS1513", 4, "Mudah",
  "#include <iostream>\nusing namespace std;\n\nvoid printStars(int n) {\n    // cetak n asterisk pada satu baris\n}\n\nint main() {\n    int n;\n    cin >> n;\n    printStars(n);\n    return 0;\n}",
  "Satu baris: integer n.", "Cetak n asterisk pada satu baris.",
  "5", "*****",
  [{"input": "5", "expected_output": "*****"},
   {"input": "1", "expected_output": "*"},
   {"input": "10", "expected_output": "**********"},
   {"input": "3", "expected_output": "***"},
   {"input": "7", "expected_output": "*******"}])

q("printLine Function",
  "Tulis fungsi void printLine() yang mencetak sebaris sempang '-----------' (11 sempang). Dalam main(), panggil fungsi ini sebanyak 3 kali.",
  "DFDS1513", 4, "Mudah",
  "#include <iostream>\nusing namespace std;\n\nvoid printLine() {\n    // cetak 11 sempang diikuti newline\n}\n\nint main() {\n    // panggil printLine() sebanyak 3 kali\n    return 0;\n}",
  "Tiada input.", "Cetak 3 baris, setiap satu mengandungi 11 sempang.",
  "", "-----------\n-----------\n-----------",
  [{"input": "", "expected_output": "-----------\n-----------\n-----------"},
   {"input": "", "expected_output": "-----------\n-----------\n-----------"},
   {"input": "", "expected_output": "-----------\n-----------\n-----------"}])

q("greetUser Function",
  "Tulis fungsi void greetUser(string name) yang mencetak 'Hello, [nama]! Welcome to UTEM.' Baca nama dari input dan panggil fungsi tersebut.",
  "DFDS1513", 4, "Mudah",
  "#include <iostream>\n#include <string>\nusing namespace std;\n\nvoid greetUser(string name) {\n    // cetak mesej Hello\n}\n\nint main() {\n    string name;\n    cin >> name;\n    greetUser(name);\n    return 0;\n}",
  "Satu perkataan: nama pengguna.", "Cetak satu baris: Hello, [nama]! Welcome to UTEM.",
  "Ahmad", "Hello, Ahmad! Welcome to UTEM.",
  [{"input": "Ahmad", "expected_output": "Hello, Ahmad! Welcome to UTEM."},
   {"input": "Siti", "expected_output": "Hello, Siti! Welcome to UTEM."},
   {"input": "John", "expected_output": "Hello, John! Welcome to UTEM."},
   {"input": "Ali", "expected_output": "Hello, Ali! Welcome to UTEM."}])

q("printSquare Function",
  "Tulis fungsi void printSquare(int side) yang mencetak grid asterisk berukuran side x side. Baca side (antara 1-5) dan panggil fungsi tersebut.",
  "DFDS1513", 4, "Sederhana",
  "#include <iostream>\nusing namespace std;\n\nvoid printSquare(int side) {\n    // cetak grid side x side menggunakan gelung\n}\n\nint main() {\n    int side;\n    cin >> side;\n    printSquare(side);\n    return 0;\n}",
  "Satu baris: integer side (1-5).", "Cetak grid asterisk side x side.",
  "3", "***\n***\n***",
  [{"input": "3", "expected_output": "***\n***\n***"},
   {"input": "1", "expected_output": "*"},
   {"input": "2", "expected_output": "**\n**"},
   {"input": "4", "expected_output": "****\n****\n****\n****"},
   {"input": "5", "expected_output": "*****\n*****\n*****\n*****\n*****"}])

print("=== DFDS1513 Ch5 (add 4 - return value functions) ===")
q("sumDigits Function",
  "Tulis fungsi int sumDigits(int n) yang mengira dan mengembalikan jumlah digit bagi n (n >= 0). Baca n dan cetak jumlah digitnya.",
  "DFDS1513", 5, "Sederhana",
  "#include <iostream>\nusing namespace std;\n\nint sumDigits(int n) {\n    // kira dan kembalikan jumlah semua digit dalam n\n}\n\nint main() {\n    int n;\n    cin >> n;\n    cout << sumDigits(n) << endl;\n    return 0;\n}",
  "Satu baris: satu integer n (>= 0).", "Cetak satu integer: jumlah semua digit n.",
  "123", "6",
  [{"input": "123", "expected_output": "6"},
   {"input": "9", "expected_output": "9"},
   {"input": "1000", "expected_output": "1"},
   {"input": "0", "expected_output": "0"},
   {"input": "999", "expected_output": "27"}])

q("isEven Function",
  "Tulis fungsi bool isEven(int n) yang mengembalikan true jika n adalah nombor genap dan false jika ganjil. Baca n dan cetak 'Even' atau 'Odd'.",
  "DFDS1513", 5, "Mudah",
  "#include <iostream>\nusing namespace std;\n\nbool isEven(int n) {\n    // kembalikan true jika n genap, false jika ganjil\n}\n\nint main() {\n    int n;\n    cin >> n;\n    if (isEven(n)) cout << \"Even\" << endl;\n    else cout << \"Odd\" << endl;\n    return 0;\n}",
  "Satu baris: satu integer n.", "Cetak 'Even' atau 'Odd'.",
  "4", "Even",
  [{"input": "4", "expected_output": "Even"},
   {"input": "7", "expected_output": "Odd"},
   {"input": "0", "expected_output": "Even"},
   {"input": "-3", "expected_output": "Odd"},
   {"input": "100", "expected_output": "Even"}])

q("celsiusToFahrenheit Function",
  "Tulis fungsi double celsiusToFahrenheit(double c) yang menukar suhu dari Celsius ke Fahrenheit. Formula: F = (c * 9/5) + 32. Cetak dengan 2 tempat perpuluhan.",
  "DFDS1513", 5, "Mudah",
  "#include <iostream>\n#include <iomanip>\nusing namespace std;\n\ndouble celsiusToFahrenheit(double c) {\n    // tukar Celsius ke Fahrenheit\n}\n\nint main() {\n    double c;\n    cin >> c;\n    cout << fixed << setprecision(2) << celsiusToFahrenheit(c) << endl;\n    return 0;\n}",
  "Satu baris: satu nombor - suhu dalam Celsius.", "Cetak satu nombor perpuluhan: suhu dalam Fahrenheit (2 d.p.).",
  "0", "32.00",
  [{"input": "0", "expected_output": "32.00"},
   {"input": "100", "expected_output": "212.00"},
   {"input": "37", "expected_output": "98.60"},
   {"input": "-40", "expected_output": "-40.00"},
   {"input": "25", "expected_output": "77.00"}])

q("circleArea Function",
  "Tulis fungsi double circleArea(double r) yang mengira luas bulatan. Formula: luas = pi * r * r dengan pi = 3.14159. Cetak dengan 2 tempat perpuluhan.",
  "DFDS1513", 5, "Mudah",
  "#include <iostream>\n#include <iomanip>\nusing namespace std;\n\ndouble circleArea(double r) {\n    const double pi = 3.14159;\n    // kira dan kembalikan luas bulatan\n}\n\nint main() {\n    double r;\n    cin >> r;\n    cout << fixed << setprecision(2) << circleArea(r) << endl;\n    return 0;\n}",
  "Satu baris: satu nombor - jejari.", "Cetak satu nombor perpuluhan: luas bulatan (2 d.p.).",
  "5", "78.54",
  [{"input": "5", "expected_output": "78.54"},
   {"input": "1", "expected_output": "3.14"},
   {"input": "7", "expected_output": "153.94"},
   {"input": "10", "expected_output": "314.16"},
   {"input": "3", "expected_output": "28.27"}])

print("=== DFDS1513 Ch6 (add 4 - pass by reference) ===")
q("getMinMax Function (Pass by Reference)",
  "Tulis fungsi void getMinMax(int a, int b, int c, int &min, int &max) yang mengisi min dan max dengan nilai terkecil dan terbesar daripada a, b, c. Baca 3 nilai dan cetak min kemudian max.",
  "DFDS1513", 6, "Sederhana",
  "#include <iostream>\nusing namespace std;\n\nvoid getMinMax(int a, int b, int c, int &minVal, int &maxVal) {\n    // tetapkan minVal dan maxVal menggunakan pass by reference\n}\n\nint main() {\n    int a, b, c, mn, mx;\n    cin >> a >> b >> c;\n    getMinMax(a, b, c, mn, mx);\n    cout << mn << endl << mx << endl;\n    return 0;\n}",
  "Satu baris: tiga integer a, b, c.", "Cetak dua baris: min pada baris pertama, max pada baris kedua.",
  "5 3 8", "3\n8",
  [{"input": "5 3 8", "expected_output": "3\n8"},
   {"input": "1 2 3", "expected_output": "1\n3"},
   {"input": "9 9 9", "expected_output": "9\n9"},
   {"input": "-1 5 0", "expected_output": "-1\n5"},
   {"input": "100 50 75", "expected_output": "50\n100"}])

q("increment Function (Pass by Reference)",
  "Tulis fungsi void increment(int &x, int amount) yang menambah x dengan amount menggunakan pass by reference. Baca x dan amount, panggil fungsi, kemudian cetak nilai x baru.",
  "DFDS1513", 6, "Mudah",
  "#include <iostream>\nusing namespace std;\n\nvoid increment(int &x, int amount) {\n    // tambah x dengan amount (pass by reference)\n}\n\nint main() {\n    int x, amount;\n    cin >> x >> amount;\n    increment(x, amount);\n    cout << x << endl;\n    return 0;\n}",
  "Satu baris: dua integer - x dan amount.", "Cetak satu integer: nilai x selepas ditambah amount.",
  "5 3", "8",
  [{"input": "5 3", "expected_output": "8"},
   {"input": "0 10", "expected_output": "10"},
   {"input": "100 -50", "expected_output": "50"},
   {"input": "7 0", "expected_output": "7"},
   {"input": "-3 3", "expected_output": "0"}])

q("squareIt Function (Pass by Reference)",
  "Tulis fungsi void squareIt(int &n) yang mengkuasaduakan n menggunakan pass by reference (ubah nilai n secara terus). Baca n, panggil fungsi, kemudian cetak nilai n baru.",
  "DFDS1513", 6, "Mudah",
  "#include <iostream>\nusing namespace std;\n\nvoid squareIt(int &n) {\n    // kuasaduakan n menggunakan pass by reference\n}\n\nint main() {\n    int n;\n    cin >> n;\n    squareIt(n);\n    cout << n << endl;\n    return 0;\n}",
  "Satu baris: satu integer n.", "Cetak satu integer: n dikuasaduakan.",
  "4", "16",
  [{"input": "4", "expected_output": "16"},
   {"input": "3", "expected_output": "9"},
   {"input": "1", "expected_output": "1"},
   {"input": "0", "expected_output": "0"},
   {"input": "5", "expected_output": "25"}])

q("divmod Function (Pass by Reference)",
  "Tulis fungsi void divmod(int a, int b, int &quotient, int &remainder) yang mengisi quotient (a/b) dan remainder (a%b) menggunakan pass by reference. Baca a dan b, cetak quotient kemudian remainder.",
  "DFDS1513", 6, "Sederhana",
  "#include <iostream>\nusing namespace std;\n\nvoid divmod(int a, int b, int &quotient, int &remainder) {\n    // tetapkan quotient dan remainder menggunakan pass by reference\n}\n\nint main() {\n    int a, b, q, r;\n    cin >> a >> b;\n    divmod(a, b, q, r);\n    cout << q << endl << r << endl;\n    return 0;\n}",
  "Satu baris: dua integer a dan b (b != 0).", "Cetak dua baris: quotient pada baris pertama, remainder pada baris kedua.",
  "10 3", "3\n1",
  [{"input": "10 3", "expected_output": "3\n1"},
   {"input": "20 4", "expected_output": "5\n0"},
   {"input": "7 2", "expected_output": "3\n1"},
   {"input": "100 7", "expected_output": "14\n2"},
   {"input": "15 5", "expected_output": "3\n0"}])

conn.commit()
conn.close()
print("\nDone! Checking counts...")

conn2 = sqlite3.connect(DB_PATH)
rows = conn2.execute("""
    SELECT course_code, chapter, COUNT(*) as cnt
    FROM question_bank
    GROUP BY course_code, chapter
    ORDER BY course_code, chapter
""").fetchall()
print("\nQuestion Bank Counts:")
for r in rows:
    print(f"  {r[0]} Ch{r[1]}: {r[2]}")
conn2.close()
