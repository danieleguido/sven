'use strict';

/**
 * @ngdoc directive
 * @name svenClientApp.directive:annotator
 * @description
 * # concepts
 */
angular.module('sven')
  .directive('annotator', function($compile) {
    return {
      restrict : 'A',
      scope:{
        content: '='
      },
      link : function(scope, element, attrs) {
        element.html(scope.content);
        $compile(element.contents())(scope);
      }
    }
  })