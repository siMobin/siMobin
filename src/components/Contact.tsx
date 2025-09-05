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
    <div
      className="p-4 bg-gray-900/50 text-white w-full flex gap-4"
      id="contact"
    >
      <div className="card">
        <h2 className="text-2xl font-bold text-blue-400 mb-4 flex items-center">
          Get In Touch
        </h2>
        <div className="flex gap-4 justify-between">
          <div className="space-y-4">
            <div className="flex items-center">
              <Mail className="mr-3 text-blue-300" />
              <div>
                <h3 className="font-semibold">Email</h3>
                <p>shakibulislammobin@gmail.com</p>
              </div>
            </div>
            <div className="flex items-center">
              <Phone className="mr-3 text-blue-300" />
              <div>
                <h3 className="font-semibold">WhatsApp</h3>
                <p>+880 1746-301800</p>
              </div>
            </div>
            <div className="flex items-center">
              <MapPin className="mr-3 text-blue-300" />
              <div>
                <h3 className="font-semibold">Location</h3>
                <p>Dhaka, Bangladesh</p>
              </div>
            </div>
          </div>

          <pre className="text-sm">
            <code className="text-sm text-code-keyword">
              {`~$ cat contact.me`}
            </code>
            <code className="text-code-string">
              {`
    Email: shakibulislammobin@gmail.com
    Phone: +880 1746-301800
    Location: Dhaka, Bangladesh`}
            </code>
          </pre>
        </div>
      </div>

      <div className="card">
        <h2 className="text-2xl font-bold text-blue-400 mb-4">
          Social Profiles
        </h2>
        <div className="flex gap-4 justify-between flex-col">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center">
              <Github className="mr-3 text-blue-300" />
              <div>
                <h3 className="font-semibold">GitHub</h3>
                <p>@siMobin</p>
              </div>
            </div>
            <div className="flex items-center">
              <Linkedin className="mr-3 text-blue-300" />
              <div>
                <h3 className="font-semibold">LinkedIn</h3>
                <p>Md. Shakibul Islam</p>
              </div>
            </div>
            <div className="flex items-center">
              <Twitter className="mr-3 text-blue-300" />
              <div>
                <h3 className="font-semibold">Twitter</h3>
                <p>@si_Mobin</p>
              </div>
            </div>
            <div className="flex items-center">
              <Facebook className="mr-3 text-blue-300" />
              <div>
                <h3 className="font-semibold">Facebook</h3>
                <p>shakibul.mobin</p>
              </div>
            </div>
          </div>

          <pre>
            <code className="text-sm text-code-keyword">{`~$ cat social_profiles.txt`}</code>
            <code className="text-sm text-code-string">
              {`
    GitHub: https://github.com/siMobin
    LinkedIn: https://www.linkedin.com/in/shakibulislammobin/
    Twitter: https://twitter.com/si_Mobin
    Facebook: https://www.facebook.com/shakibul.mobin`}
            </code>
          </pre>
        </div>
      </div>
    </div>
  );
};

export default Contact;
