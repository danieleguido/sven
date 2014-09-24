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
        data: '=',
        measure: '=',
        groups: '='
      },
      link: function postLink(scope, element, attrs) {
        var matrix = snark
            .matrix()
            .init(d3.select(".viewer"));
        


        var render = function() {
          // get positions for each set
        
          if(scope.data)
            matrix
              .data(scope.data)
              .update({ measure:scope.measure||'tf'})
          
        }



        scope.$watch('data', render, true);

        scope.$watch('measure', render, true);
      }
    };
  });
