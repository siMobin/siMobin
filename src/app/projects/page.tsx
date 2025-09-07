import GitHubProjects from "@/components/GitHubProjects";
import Footer from "@/components/Footer";
import Header from "@/components/Header";

export default function Projects() {
  return (
    <div className="">
      {/* Header */}
      <Header />
      <section className="flex flex-col items-center justify-center flex-grow my-8 pb-8 bg-accent/5">
        <GitHubProjects limit={30} />
      </section>
      <Footer />
    </div>
  );
}
