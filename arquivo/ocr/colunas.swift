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
  let edges:[CGFloat] = arg.contains("Carros") ? [0.048,0.067,0.103,0.183,0.294,0.333,0.413,0.516,0.554,0.64,0.693,0.767,0.951] : [0.044,0.075,0.129,0.268,0.422,0.492,0.553,0.629,0.951]
  for c in 0..<(edges.count-1) {
   let x=edges[c]*CGFloat(w), cw=(edges[c+1]-edges[c])*CGFloat(w)
   let crop=img.cropping(to:CGRect(x:x,y:0,width:cw,height:CGFloat(h)))!
   let req=VNRecognizeTextRequest(); req.recognitionLevel = .accurate;req.recognitionLanguages=["pt-BR","en-US"];req.usesLanguageCorrection=false
   try VNImageRequestHandler(cgImage:crop).perform([req])
   for o in req.results ?? [] { all.append(["page":i+1,"col":c,"x":edges[c]+o.boundingBox.minX*(edges[c+1]-edges[c]),"y":o.boundingBox.midY,"w":o.boundingBox.width*(edges[c+1]-edges[c]),"h":o.boundingBox.height,"text":o.topCandidates(1).first?.string ?? ""]) }
  }
  if i==0 {let rep=NSBitmapImageRep(cgImage:img);try rep.representation(using:.png,properties:[:])!.write(to:URL(fileURLWithPath:"tmp/analise/"+u.deletingPathExtension().lastPathComponent+".png"))}
 }
 try JSONSerialization.data(withJSONObject:all).write(to:URL(fileURLWithPath:"tmp/analise/"+u.deletingPathExtension().lastPathComponent+"_cols.json"))
 try s.write(to:URL(fileURLWithPath:"tmp/analise/"+u.deletingPathExtension().lastPathComponent+"_cols.txt"),atomically:true,encoding:.utf8)
 print("\(arg): \(d.pageCount) páginas, \(s.count) caracteres");fflush(stdout)
}
