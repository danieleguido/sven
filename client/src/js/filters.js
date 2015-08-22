'use strict';

/**
 * @ngdoc filter
 * @name svenClientApp.filter:tag
 * @function
 * @description
 * # tag
 * Filter in the svenClientApp.
 */
angular.module('sven')
  .filter('tag', function () {
    return function (input) {
      return input.split(' - ').shift();
    };
  })
  .filter('percentage', function () {
    return function (input) {
      return (Math.ceil(input*10000)/100) + '%';
    };
  })
  .filter('cmd', function () {
    return function (input) {
      return input.match(/--cmd\s+([a-z]*) -/)[1];
    };
  })
  .filter('htmltext', function () {
    return function (input) {
      input = input || '';
      return input.replace(/\n\n+/g,'\n\n').split('\n').join('<br/>');
    };
  })
  .filter('humanized', function () {
    return function (input, filterKey) {

      return input + ' (' + filterKey.split('_').map(function(d) {
        if(['content', 'slug', 'segments'].indexOf(d) !== -1)
          return ''
        return d
      }).join(' ') + ')'
      
    };
  })
  .filter('truncate', function(){
    return function truncate(text, maxLength, delimiter, overflow) {
      delimiter = delimiter || "...";
      overflow = overflow || false;
      var ret = text;
      if (ret.length > maxLength) {
        var breakpoint = overflow ? maxLength + ret.substr(maxLength).indexOf(" ") : ret.substr(0, maxLength).lastIndexOf(" ");
        ret = ret.substr(0, breakpoint) + delimiter;
      }
      return ret;
    }
  })
  // convert tsv strings into well formatted javascript objects
  .filter('tsv', function() {
    return function(input) {
        var lines     = input.split(/[\n\r]+/),
            separator = '\t',
            result    = {
              headers: [],
              rows: []
            },
            numlines = 0;

        if(!lines.length) 
          return;

        result.headers = lines.shift().split(separator);
        numlines = Math.min(lines.length, 25);
        for (var i=0; i<numlines; i++) {
          result.rows.push(lines[i].split(separator));
        };

        return result;
      };
  });
