import Foundation
import PDFKit
import Vision
import AppKit
for arg in CommandLine.arguments.dropFirst() {
 let u=URL(fileURLWithPath:arg); guard let d=PDFDocument(url:u) else {continue}
 var s=""; var all:[[String:Any]]=[]
 for i in 0..<d.pageCount {
  let page=d.page(at:i)!
  let b=page.bounds(for:.mediaBox); let scale:CGFloat=5
  let w=Int(b.width*scale), h=Int(b.height*scale)
  let ctx=CGContext(data:nil,width:w,height:h,bitsPerComponent:8,bytesPerRow:0,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue)!
  ctx.setFillColor(NSColor.white.cgColor);ctx.fill(CGRect(x:0,y:0,width:w,height:h));ctx.scaleBy(x:scale,y:scale);page.draw(with:.mediaBox,to:ctx)
  let img=ctx.makeImage()!
  let req=VNRecognizeTextRequest();req.recognitionLevel = .accurate;req.recognitionLanguages=["pt-BR","en-US"];req.usesLanguageCorrection=false
  try VNImageRequestHandler(cgImage:img).perform([req])
  for o in req.results ?? [] { all.append(["page":i+1,"x":o.boundingBox.minX,"y":o.boundingBox.midY,"w":o.boundingBox.width,"h":o.boundingBox.height,"text":o.topCandidates(1).first?.string ?? ""]) }
  s += "\n=== PÁGINA \(i+1) ===\n" + (req.results ?? []).compactMap{$0.topCandidates(1).first?.string}.joined(separator:"\n")+"\n"
  if i==0 {let rep=NSBitmapImageRep(cgImage:img);try rep.representation(using:.png,properties:[:])!.write(to:URL(fileURLWithPath:"tmp/analise/"+u.deletingPathExtension().lastPathComponent+".png"))}
 }
 try JSONSerialization.data(withJSONObject:all).write(to:URL(fileURLWithPath:"tmp/analise/"+u.deletingPathExtension().lastPathComponent+".json"))
 try s.write(to:URL(fileURLWithPath:"tmp/analise/"+u.deletingPathExtension().lastPathComponent+".txt"),atomically:true,encoding:.utf8)
 print("\(arg): \(d.pageCount) páginas, \(s.count) caracteres");fflush(stdout)
}
