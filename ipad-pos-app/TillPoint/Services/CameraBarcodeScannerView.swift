import SwiftUI
import AVFoundation

/// Fallback barcode scanning using the iPad's built-in camera, for when no
/// Bluetooth scanner is paired, or for one-off barcode lookups while editing a product.
struct CameraBarcodeScannerView: UIViewControllerRepresentable {
    var onScan: (String) -> Void

    func makeUIViewController(context: Context) -> ScannerViewController {
        let vc = ScannerViewController()
        vc.onScan = onScan
        return vc
    }

    func updateUIViewController(_ uiViewController: ScannerViewController, context: Context) {}

    final class ScannerViewController: UIViewController, AVCaptureMetadataOutputObjectsDelegate {
        var onScan: ((String) -> Void)?
        private let session = AVCaptureSession()
        private var hasScanned = false

        override func viewDidLoad() {
            super.viewDidLoad()
            view.backgroundColor = .black
            guard let device = AVCaptureDevice.default(for: .video),
                  let input = try? AVCaptureDeviceInput(device: device) else { return }

            if session.canAddInput(input) { session.addInput(input) }

            let output = AVCaptureMetadataOutput()
            if session.canAddOutput(output) {
                session.addOutput(output)
                output.setMetadataObjectsDelegate(self, queue: .main)
                output.metadataObjectTypes = [.ean13, .ean8, .upce, .code128, .code39, .qr]
            }

            let previewLayer = AVCaptureVideoPreviewLayer(session: session)
            previewLayer.videoGravity = .resizeAspectFill
            previewLayer.frame = view.bounds
            view.layer.addSublayer(previewLayer)
        }

        override func viewDidAppear(_ animated: Bool) {
            super.viewDidAppear(animated)
            hasScanned = false
            if !session.isRunning {
                DispatchQueue.global(qos: .userInitiated).async { self.session.startRunning() }
            }
        }

        override func viewDidDisappear(_ animated: Bool) {
            super.viewDidDisappear(animated)
            if session.isRunning { session.stopRunning() }
        }

        override func viewDidLayoutSubviews() {
            super.viewDidLayoutSubviews()
            view.layer.sublayers?.first?.frame = view.bounds
        }

        func metadataOutput(_ output: AVCaptureMetadataOutput, didOutput metadataObjects: [AVMetadataObject], from connection: AVCaptureConnection) {
            guard !hasScanned,
                  let object = metadataObjects.first as? AVMetadataMachineReadableCodeObject,
                  let value = object.stringValue else { return }
            hasScanned = true
            onScan?(value)
        }
    }
}
