| toolkit | widget | label | AT-SPI role | name | Text.get_text plaintext | text-changed plaintext | H_role | H_orca | H_orca+label |
|---|---|---|---|---|---|---|---|---|---|
| gtk3 3.24.49 | Gtk.Entry visibility=False | Password | password text | '' | masked | masked | True | True | True |
| gtk3 3.24.49 | Gtk.Entry visibility=False | Account key | password text | '' | masked | masked | True | True | True |
| gtk4 4.18.6 | Gtk.PasswordEntry | Password | password text | 'Password' | PLAINTEXT | PLAINTEXT | True | True | True |
| gtk4 4.18.6 | Gtk.Entry visibility=False | Account key | text | 'Account key' | PLAINTEXT | PLAINTEXT | False | False | False |
| chrome 1.0 | <input type=password> |  | password text | 'Password' | masked | masked | True | True | True |
| chrome 1.0 | <input type=password> |  | password text | 'Account key' | masked | masked | True | True | True |
| firefox 140.15.0 | <input type=password> | Password | password text | 'Password' | masked | masked | True | True | True |
| firefox 140.15.0 | <input type=password> | Account key | password text | 'Account key' | masked | masked | True | True | True |

rep1 == rep2 (all fields identical): True; Atspi.StateType.PROTECTED present: False; libatspi (major=2, minor=56, micro=2)
masked fields: 8; fields with plaintext in Text.get_text: 2; fields with plaintext in events: 2; snapshot plaintext missed by H_orca: 1; event plaintext missed by a source-role filter: 1; masked text length == secret length: 8/8
