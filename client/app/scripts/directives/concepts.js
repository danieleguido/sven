'use strict';

/**
 * @ngdoc directive
 * @name svenClientApp.directive:concepts
 * @description
 * # concepts
 */
angular.module('svenClientApp')
  .directive('concepts', function () {
    return {
      template: '<div class="viewer"></div>',
      restrict: 'E',
      scope: {
        data: '='
      },
      link: function postLink(scope, element, attrs) {
        var matrix = snark
            .matrix()
            .init(d3.select(".viewer"));
        
        var render = function(data) {
          // get positions for each set
          console.log('rendering', data)
        }

        scope.$watch('data', function(data) {
          if(data)
            matrix
              .data(data)
              .update()
        }, true);
      }
    };
  });
