import Foundation
import PDFKit
for arg in CommandLine.arguments.dropFirst() {
 let u = URL(fileURLWithPath: arg)
 guard let d = PDFDocument(url:u) else { continue }
 var s = ""
 for i in 0..<d.pageCount { s += "\n=== PÁGINA \(i+1) ===\n" + (d.page(at:i)?.string ?? "") + "\n" }
 try s.write(to:URL(fileURLWithPath:"tmp/analise/"+u.deletingPathExtension().lastPathComponent+".txt"), atomically:true, encoding:.utf8)
 print("\(arg): \(d.pageCount) páginas, \(s.count) caracteres")
}
