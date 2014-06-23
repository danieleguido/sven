module.exports = function(grunt) {
  grunt.initConfig({
    less: {
      development: {
        options: {
          compress: false
        },
        files: {
          "./src/build/css/style.css": "src/less/style.less"
        }
      },
      production: {
        options: {
          compress:true,
          cleancss: true
        },
        files: {
          "./src/build/css/style.min.css": "src/less/style.less"
        }
      }
    },
    pkg: grunt.file.readJSON('./package.json'),
    uglify: {
      options: {
        banner: '/*\n\n    Sven  \n    ================================\n\n<%= pkg.description %> - Version: <%= pkg.version %> */\n'
      },
      production: {
        files: {
          './src/build/js/sven.min.js': [
            './src/libs/*.js',
            './src/js/*.js'
          ]
        }
      }
    }
  });

  console.log("\n                      *     .--.\n                           / /  `\n          +               | |\n                 '         \\ \\__,\n             *          +   '--'  *\n                 +   /\\\n    +              .'  '.   *\n           *      /======\\      +\n                 ;:.  _   ;\n                 |:. (_)  |\n                 |:.  _   |\n       +         |:. (_)  |          *\n                 ;:.      ;\n               .' \:.    /  `.\n              / .-'':._.'`-. \\\n              |/    /||\\    \\|\n        jgs _..--\"\"\"````\"\"\"--.._\n      _.-'``                    ``'-._\n    -'                                '-\n\n");
  console.log(grunt.cli.tasks.join(''));

  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-less');

  grunt.registerTask('default', ['less:development','uglify:production']);
  grunt.registerTask('production', ['less:production','uglify:production']);
  
};
