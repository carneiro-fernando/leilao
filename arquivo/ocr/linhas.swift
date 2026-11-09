import Foundation
import PDFKit
import Vision
import AppKit
for arg in CommandLine.arguments.dropFirst() {
 let u=URL(fileURLWithPath:arg); guard let d=PDFDocument(url:u) else {continue}
 var s=""; var all:[[String:Any]]=[]
 for i in 0..<d.pageCount {
  let page=d.page(at:i)!
  let b=page.bounds(for:.mediaBox); let scale:CGFloat=3
  let w=Int(b.width*scale), h=Int(b.height*scale)
  let ctx=CGContext(data:nil,width:w,height:h,bitsPerComponent:8,bytesPerRow:0,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue)!
  ctx.setFillColor(NSColor.white.cgColor);ctx.fill(CGRect(x:0,y:0,width:w,height:h));ctx.scaleBy(x:scale,y:scale);page.draw(with:.mediaBox,to:ctx)
  let img=ctx.makeImage()!
  let ptr=ctx.data!.assumingMemoryBound(to:UInt8.self)
  let stride=ctx.bytesPerRow
  var lines:[Int]=[]
  for yy in 0..<h {
   var dark=0
   for xx in Int(Double(w)*0.05)..<Int(Double(w)*0.95) { let p=yy*stride+xx*4; if Int(ptr[p])+Int(ptr[p+1])+Int(ptr[p+2])<400 {dark += 1} }
   if Double(dark)/Double(w)>0.65 { if lines.last == nil || yy-lines.last!>3 {lines.append(yy)} }
  }
  all.append(["page":i+1,"height":h,"lines":lines])
  if i==0 {let rep=NSBitmapImageRep(cgImage:img);try rep.representation(using:.png,properties:[:])!.write(to:URL(fileURLWithPath:"tmp/analise/"+u.deletingPathExtension().lastPathComponent+".png"))}
 }
 try JSONSerialization.data(withJSONObject:all).write(to:URL(fileURLWithPath:"tmp/analise/"+u.deletingPathExtension().lastPathComponent+"_lines.json"))
 try s.write(to:URL(fileURLWithPath:"tmp/analise/"+u.deletingPathExtension().lastPathComponent+"_lines.txt"),atomically:true,encoding:.utf8)
 print("\(arg): \(d.pageCount) páginas, \(s.count) caracteres");fflush(stdout)
}
