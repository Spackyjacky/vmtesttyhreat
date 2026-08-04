import SwiftUI
import MessageUI

struct MailComposerView: UIViewControllerRepresentable {
    let recipient: String
    let subject: String
    let body: String
    var onFinish: (() -> Void)?

    static func canSendMail() -> Bool { MFMailComposeViewController.canSendMail() }

    func makeUIViewController(context: Context) -> MFMailComposeViewController {
        let vc = MFMailComposeViewController()
        vc.mailComposeDelegate = context.coordinator
        vc.setToRecipients([recipient])
        vc.setSubject(subject)
        vc.setMessageBody(body, isHTML: false)
        return vc
    }

    func updateUIViewController(_ uiViewController: MFMailComposeViewController, context: Context) {}

    func makeCoordinator() -> Coordinator { Coordinator(onFinish: onFinish) }

    final class Coordinator: NSObject, MFMailComposeViewControllerDelegate {
        let onFinish: (() -> Void)?
        init(onFinish: (() -> Void)?) { self.onFinish = onFinish }

        func mailComposeController(_ controller: MFMailComposeViewController, didFinishWith result: MFMailComposeResult, error: Error?) {
            controller.dismiss(animated: true) { self.onFinish?() }
        }
    }
}
