import React from "react";
import {
  Mail,
  Phone,
  MapPin,
  Github,
  Linkedin,
  Twitter,
  Facebook,
} from "lucide-react";

const Contact: React.FC = () => {
  return (
    <main
      className="p-4 pb-0 relative overflow-clip bg-gray-900/50 text-white w-full space-y-4 flex gap-4"
      id="contact"
    >
      <div className="flex flex-col justify-evenly gap-8 flex-1">
        {/*  */}
        <div className="space-y-4">
          <h1 className="text-6xl font-extrabold text-accent">
            Available At Any Time, Any Where, Any Project...
          </h1>
          <p className="text-lg opacity-80">
            Lorem ipsum dolor sit amet consectetur, adipisicing elit. Doloribus
            dignissimos accusamus quam odit laborum unde, at dicta nemo esse
            eius?
          </p>
        </div>
        {/*  */}

        <pre className="contact">
          <span className="text-keyword">~$ cat contact.me</span>
          <br />
          <code className="text-string">
            &nbsp;&nbsp; Email:{" "}
            <a
              href="mailto:shakibulislammobin@gmail.com"
              className="!text-string"
            >
              shakibulislammobin@gmail.com
            </a>
            <br />
            &nbsp;&nbsp; Phone:{" "}
            <a href="tel:+8801746301800" className="!text-string">
              +8801746301800
            </a>
            <br />
            &nbsp;&nbsp; Discord:{" "}
            <a href="#" className="!text-string">
              shakibulislammobin
            </a>
          </code>
        </pre>
      </div>

      {/*  */}

      <div className="flex-1">
        <img
          src="./images/gif.webp"
          alt=""
          className="w-[650px] absolute bottom-[-18px] right-[-5px]"
        />
      </div>
    </main>
  );
};

export default Contact;
