'use strict';

/**
 * @ngdoc directive
 * @name svenClientApp.directive:concepts
 * @description
 * # concepts
 */
angular.module('svenClientApp')
  .directive('network', function () {
    return {
      template: '<div class="viewer"></div>',
      restrict: 'E',
      scope: {
        data: '=',
        measure: '='
      },
      link: function postLink(scope, element, attrs) {
        var matrix = snark
            .matrix()
            .init(d3.select(".viewer"));
        


        var render = function() {
          if(scope.data)
            matrix
              .data(scope.data)
              .update()
        }

        scope.$watch('data', render, true);

        scope.$watch('measure', render, true);
      }
    };
  });