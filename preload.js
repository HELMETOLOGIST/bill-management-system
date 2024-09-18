window.addEventListener('DOMContentLoaded', () => {
  // Function to load external CSS files
  function loadCSS(href, callback) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = href;
      link.onload = () => {
          if (callback) callback();
      };
      link.onerror = () => {
          console.error(`Failed to load CSS: ${href}`);
      };
      document.head.appendChild(link);
  }

  // Function to load external JavaScript files
  function loadScript(src, callback) {
      const script = document.createElement('script');
      script.src = src;
      script.onload = () => {
          if (callback) callback();
      };
      script.onerror = () => {
          console.error(`Failed to load script: ${src}`);
      };
      document.head.appendChild(script);
  }

  // Load valid CSS files
  loadCSS('https://cdnjs.cloudflare.com/ajax/libs/toastr.js/latest/toastr.min.css');

  // Load valid JavaScript files
  loadScript('https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js', () => {
      loadScript('https://cdnjs.cloudflare.com/ajax/libs/jquery-validate/1.19.5/jquery.validate.min.js', () => {
          loadScript('https://cdnjs.cloudflare.com/ajax/libs/toastr.js/latest/toastr.min.js', () => {
              console.log('All scripts and styles loaded successfully');
          });
      });
  });
});
