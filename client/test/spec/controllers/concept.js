'use strict';

describe('Controller: ConceptCtrl', function () {

  // load the controller's module
  beforeEach(module('svenClientApp'));

  var ConceptCtrl,
    scope;

  // Initialize the controller and a mock scope
  beforeEach(inject(function ($controller, $rootScope) {
    scope = $rootScope.$new();
    ConceptCtrl = $controller('ConceptCtrl', {
      $scope: scope
    });
  }));

  it('should attach a list of awesomeThings to the scope', function () {
    expect(scope.awesomeThings.length).toBe(3);
  });
});
