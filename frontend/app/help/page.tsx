"use client"

import { MainLayout } from "@/components/main-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Code, MessageSquare, Settings, Mic, FileText, Clock } from "lucide-react"

const features = [
  {
    icon: Code,
    title: "Technical Interviews",
    description:
      "Practice coding problems with real-time syntax highlighting. The AI interviewer will guide you through the problem, ask clarifying questions, and evaluate your solution approach.",
  },
  {
    icon: MessageSquare,
    title: "Behavioral Interviews",
    description:
      "Practice answering behavioral questions using the STAR method. The AI will ask follow-up questions to help you elaborate on your experiences.",
  },
  {
    icon: Mic,
    title: "Voice Interaction",
    description:
      "Speak naturally with the AI interviewer using voice input. The system will transcribe your responses and provide audio feedback.",
  },
  {
    icon: FileText,
    title: "Resume Integration",
    description:
      "Upload your resume to receive personalized interview questions based on your experience and the roles you are targeting.",
  },
  {
    icon: Settings,
    title: "Customizable Difficulty",
    description:
      "Adjust the difficulty level from intern to staff engineer. Questions and expectations will be calibrated to your target role.",
  },
  {
    icon: Clock,
    title: "Session Tracking",
    description:
      "Track your interview practice sessions, review past transcripts, and monitor your progress over time.",
  },
]

const faqs = [
  {
    question: "How do I start a technical interview?",
    answer:
      "Navigate to the Technical page from the sidebar, then click the \"Start Interview\" button. You will be presented with a coding problem and can interact with the AI interviewer via voice or text.",
  },
  {
    question: "Can I use any programming language?",
    answer:
      "Yes! The code editor supports syntax highlighting for multiple languages including JavaScript, Python, Java, and more. You can write your solution in whichever language you prefer.",
  },
  {
    question: "How does the voice agent work?",
    answer:
      "The voice agent uses speech-to-text and text-to-speech technology to enable natural conversation. Click the microphone button to speak, and the AI will respond with audio.",
  },
  {
    question: "What is the STAR method?",
    answer:
      "STAR stands for Situation, Task, Action, Result. It is a structured way to answer behavioral interview questions by describing a specific situation, your task, the actions you took, and the results you achieved.",
  },
  {
    question: "How do I adjust the difficulty level?",
    answer:
      "Go to Settings and select your target experience level (Intern through Staff+). This will adjust the complexity of questions and the expectations for your answers.",
  },
  {
    question: "Is my data saved between sessions?",
    answer:
      "Yes, if you have auto-save enabled in Settings. Your code, notes, and session history are stored locally. You can also export your session data for review.",
  },
  {
    question: "Can I review past interview sessions?",
    answer:
      "Yes! All your past sessions are available on the Home page. You can review the transcript, your code submissions, and any notes you made during the session.",
  },
]

export default function HelpPage() {
  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <h1 className="text-2xl font-semibold text-foreground tracking-tight">Help Center</h1>
          <p className="text-muted-foreground mt-1">
            Learn how to make the most of InterviewPro
          </p>
        </div>

        {/* About Section */}
        <Card>
          <CardHeader>
            <CardTitle>About InterviewPro</CardTitle>
            <CardDescription>Your AI-powered interview practice companion</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-foreground/90 leading-relaxed">
              InterviewPro is an AI-powered platform designed to help you prepare for technical and
              behavioral interviews. Practice coding problems with an AI interviewer who guides you
              through the problem-solving process, asks clarifying questions, and provides feedback
              on your approach. For behavioral interviews, practice answering common questions using
              the STAR method with real-time voice interaction.
            </p>
          </CardContent>
        </Card>

        {/* Features */}
        <div>
          <h2 className="text-lg font-medium text-foreground mb-4">Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {features.map((feature) => (
              <Card key={feature.title}>
                <CardContent className="flex gap-4 p-4">
                  <div className="p-2 bg-secondary rounded-lg h-fit">
                    <feature.icon className="h-5 w-5 text-foreground" />
                  </div>
                  <div>
                    <h3 className="font-medium text-foreground">{feature.title}</h3>
                    <p className="text-sm text-muted-foreground mt-1">{feature.description}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Quick Start Guide */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Start Guide</CardTitle>
            <CardDescription>Get started in 3 easy steps</CardDescription>
          </CardHeader>
          <CardContent>
            <ol className="space-y-4">
              <li className="flex gap-4">
                <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground text-sm font-medium shrink-0">
                  1
                </span>
                <div>
                  <p className="font-medium text-foreground">Configure your settings</p>
                  <p className="text-sm text-muted-foreground">
                    Go to Settings and select your experience level. Optionally upload your resume
                    for personalized questions.
                  </p>
                </div>
              </li>
              <li className="flex gap-4">
                <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground text-sm font-medium shrink-0">
                  2
                </span>
                <div>
                  <p className="font-medium text-foreground">Choose your interview type</p>
                  <p className="text-sm text-muted-foreground">
                    Select Technical for coding problems or Behavioral for soft skills practice from
                    the sidebar.
                  </p>
                </div>
              </li>
              <li className="flex gap-4">
                <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground text-sm font-medium shrink-0">
                  3
                </span>
                <div>
                  <p className="font-medium text-foreground">Start practicing</p>
                  <p className="text-sm text-muted-foreground">
                    Click Start Interview and begin your practice session. Use voice or text to
                    interact with the AI interviewer.
                  </p>
                </div>
              </li>
            </ol>
          </CardContent>
        </Card>

        {/* FAQ */}
        <div>
          <h2 className="text-lg font-medium text-foreground mb-4">Frequently Asked Questions</h2>
          <Card>
            <CardContent className="p-0">
              <Accordion type="single" collapsible className="w-full">
                {faqs.map((faq, index) => (
                  <AccordionItem key={index} value={`item-${index}`}>
                    <AccordionTrigger className="px-4 hover:no-underline">
                      <span className="text-left font-medium">{faq.question}</span>
                    </AccordionTrigger>
                    <AccordionContent className="px-4 pb-4">
                      <p className="text-muted-foreground">{faq.answer}</p>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </CardContent>
          </Card>
        </div>

        {/* Contact */}
        <Card>
          <CardHeader>
            <CardTitle>Need More Help?</CardTitle>
            <CardDescription>We are here to assist you</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-foreground/90">
              If you have questions not covered here, please reach out to our support team at{" "}
              <span className="text-primary font-medium">support@interviewpro.app</span>. We
              typically respond within 24 hours.
            </p>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
