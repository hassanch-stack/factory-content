import ContentEditor from "./ContentEditor";

export default function EditorPage({ params }: { params: { contentId: string } }) {
  return <ContentEditor contentId={params.contentId} />;
}
