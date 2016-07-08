var gulp  = require('gulp'),
    pkg   = require('./package.json'),
    _     = require('lodash'),
    
    // files = require('./src/files').development,
    $     = require('gulp-load-plugins')({
              rename: {
                'gulp-angular-templatecache': 'templatecache'
              }
            });
// console.log(files)
// Files
var banner = '/* resume - Version: ' + pkg.version + ' - Author: danieleguido (Daniele Guido) */\n';




gulp.task('templates', function () {
  return gulp.src('./src/templates/**/*.html')
    .pipe($.templatecache({
      module: 'miller',
      transformUrl: function(url) {
        return '/static/templates/' + url;
      }
    }))
    .pipe(gulp.dest('./src/js'))
    .pipe($.size({templates: 'js'}))
});


gulp.task('libs', function() {
  return gulp.src([
    './src/js/lib/jquery-2.2.1.min.js',
    './src/js/lib/md5.js',
    './src/js/lib/lodash.custom.min.js',
    // './src/js/lib/marked.min.js',
    './src/js/lib/markdown-it.min.js',
    './src/js/lib/markdown-it-footnote.min.js',
    './src/js/lib/simplemde.min.js',
    './src/js/lib/bibtexParse.js',
    

    './src/js/lib/angular.min.js', 
    './src/js/lib/angular-route.min.js', 
    './src/js/lib/angular-resource.min.js', 
    './src/js/lib/angular-cookies.min.js', 
    './src/js/lib/angular-sanitize.min.js', 

    './src/js/lib/angular-disqus.min.js',
    // './src/js/lib/angular-animate.min.js',
    './src/js/lib/angular-ui-router.min.js', 
    './src/js/lib/angular-strap.min.js',
    './src/js/lib/angular-strap.tpl.min.js',
    './src/js/lib/angular-elastic.js',
    './src/js/lib/angular-embedly.min.js',
    './src/js/lib/angular-embed.min.js',

    './src/js/lib/angular-local-storage.min.js',
    './src/js/lib/angular-translate.min.js',
    './src/js/lib/angular-translate-loader-static-files.min.js',
    './src/js/lib/ng-tags-input.min.js',
  ])
    .pipe($.concat('scripts.lib.min.js'))
    // .pipe($.uglify())
    // Output files
    .pipe(gulp.dest('./src/js'))
    .pipe($.size({title: 'js'}))
});

gulp.task('scripts', function() {
  return gulp.src([
      './src/js/app.js',
      './src/js/filters.js',
      './src/js/services.js',
      './src/js/templates.js',
      './src/js/controllers/*.js',
      './src/js/directives/*.js',
    ])
    .pipe($.concat('scripts.min.js'))
    // .pipe($.uglify())
    // Output files
    .pipe(gulp.dest('./src/js'))
    .pipe($.size({title: 'js'}))
});

// Lint Javascript
gulp.task('jshint', function() {
  return gulp.src([
      './src/js/app.js',
      './src/js/filters.js',
      './src/js/services.js',
      './src/js/templates.js',
      './src/js/controllers/*.js',
      './src/js/directives/*.js',
    ])
    .pipe($.jshint())
    .pipe($.jshint.reporter('jshint-stylish'))
});

// // copy and optimize stylesheet
// gulp.task('styles', function() {
//   return gulp.src('./client/src/css/*')
//     .pipe($.if('*.css', $.minifyCss()))
//       // Output files
//     .pipe(gulp.dest('./client/dist/css'))
//     .pipe($.size({title: 'styles'}));
// });

// // Optimize images
// gulp.task('images', function() {
//   return gulp.src('./client/src/images/*')
//     .pipe(gulp.dest('./client/dist/images'))
//     .pipe($.size({title: 'images'}));
// });

// // Copy web fonts to dist
// gulp.task('fonts', function() {
//   return gulp.src(['./client/src/fonts/**'])
//     .pipe(gulp.dest('./client/dist/fonts'))
//     .pipe($.size({title: 'fonts'}));
// });

// // copy (compress) locale to dist
// gulp.task('locale', function() {
//   return gulp.src(['./client/src/locale/*.json'])
//     .pipe($.jsonminify())
//     .pipe(gulp.dest('./client/dist/locale'))
//     .pipe($.size({title: 'locale'}));
// });
// // Build
// gulp.task('build', function() {
  
// });

// Default
gulp.task('default', ['templates', 'libs', 'scripts']);



