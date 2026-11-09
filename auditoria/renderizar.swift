import Foundation
import PDFKit
import AppKit
let samples=[("Carros_lista.pdf",0),("Edital.pdf",9),("Resolucao_Contran.pdf",2),("Resolucao_SGGD.pdf",1),("comprovacao_de_propriedade.pdf",0)]
for (f,i) in samples {
 let d=PDFDocument(url:URL(fileURLWithPath:f))!;let p=d.page(at:i)!;let b=p.bounds(for:.mediaBox);let scale:CGFloat=2
 let ctx=CGContext(data:nil,width:Int(b.width*scale),height:Int(b.height*scale),bitsPerComponent:8,bytesPerRow:0,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue)!
 ctx.setFillColor(NSColor.white.cgColor);ctx.fill(CGRect(x:0,y:0,width:CGFloat(ctx.width),height:CGFloat(ctx.height)));ctx.scaleBy(x:scale,y:scale);p.draw(with:.mediaBox,to:ctx)
 let rep=NSBitmapImageRep(cgImage:ctx.makeImage()!); try rep.representation(using:.png,properties:[:])!.write(to:URL(fileURLWithPath:"auditoria/"+f+".png"))
}
